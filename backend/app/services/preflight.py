"""
Pre-flight checks: the competition must not go live with unresolved configuration.
`run_preflight(settings, db)` returns [{"check", "ok", "detail", "blocking"}]. Detail never contains secrets/labels.
"""
import os
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.models.models import Competition, RubricVersion

STAGE1_WEIGHT_KEYS = ("weight_accuracy", "weight_tool", "weight_constraint", "weight_quality", "weight_efficiency")
STAGE2_WEIGHT_KEYS = ("weight_stage2_tsr", "weight_stage2_outcome", "weight_stage2_reliability",
                      "weight_stage2_tool", "weight_stage2_safety", "weight_stage2_efficiency")


def _c(name: str, ok: bool, detail: str, blocking: bool = True) -> Dict[str, Any]:
    return {"check": name, "ok": bool(ok), "detail": detail, "blocking": blocking}


def weights_sum_ok(rubric: Dict[str, Any], keys) -> bool:
    try:
        return abs(sum(float(rubric.get(k, 0)) for k in keys) - 1.0) < 1e-6
    except (TypeError, ValueError):
        return False


def run_preflight(cfg, db: Session) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    prod = cfg.ENVIRONMENT.lower() == "production"
    out.append(_c("environment_is_production", prod, cfg.ENVIRONMENT, blocking=False))
    out.append(_c("secret_key_strong", len(cfg.SECRET_KEY) >= 32 and "change" not in cfg.SECRET_KEY.lower()
                  and not cfg.SECRET_KEY.startswith("agentscore_super"), "length/default check"))
    from app.core.passwords import ITERATIONS, RECOMMENDED_ITERATIONS
    out.append(_c("password_hash_iterations", ITERATIONS >= RECOMMENDED_ITERATIONS, f"{ITERATIONS} (>= {RECOMMENDED_ITERATIONS} required)"))
    out.append(_c("database_not_sqlite", "sqlite" not in cfg.DATABASE_URL, "PostgreSQL required for the event"))
    out.append(_c("demo_seed_disabled", not cfg.SEED_DEMO_DATA, "SEED_DEMO_DATA"))
    out.append(_c("inline_evaluation_disabled", not cfg.EVALUATE_INLINE, "EVALUATE_INLINE (worker-only scoring)"))
    out.append(_c("provisional_leaderboard_disabled", not cfg.PUBLIC_PROVISIONAL_LEADERBOARD, "PUBLIC_PROVISIONAL_LEADERBOARD"))
    out.append(_c("snapshot_approval_required", not cfg.AUTO_PUBLISH_SNAPSHOTS, "AUTO_PUBLISH_SNAPSHOTS"))
    out.append(_c("stage2_https_only", cfg.STAGE2_REQUIRE_HTTPS and not cfg.STAGE2_ALLOW_LOCALHOST_DEV, "STAGE2_REQUIRE_HTTPS / ALLOW_LOCALHOST_DEV"))
    out.append(_c("cors_has_no_localhost", not any("localhost" in o or "127.0.0.1" in o for o in cfg.cors_origin_list), "CORS_ORIGINS"))

    gt = cfg.GROUND_TRUTH_PATH
    out.append(_c("ground_truth_configured", bool(gt) and os.path.exists(gt), "GROUND_TRUTH_PATH exists" if gt else "GROUND_TRUTH_PATH not set"))
    suite = cfg.STAGE2_SUITE_PATH
    suite_ok, suite_detail = False, "STAGE2_SUITE_PATH not set"
    if suite and os.path.exists(suite):
        try:
            import json
            from evaluator.stage2.evaluator import validate_test_suite
            validate_test_suite(json.load(open(suite, encoding="utf-8")))
            suite_ok, suite_detail = True, "suite valid (every task has assertions)"
        except Exception as e:
            suite_detail = f"suite invalid: {str(e).split(':')[0]}"
    out.append(_c("stage2_suite_valid", suite_ok, suite_detail))

    comp = db.query(Competition).first()
    out.append(_c("competition_exists", comp is not None, "competition row"))
    if comp:
        out.append(_c("deadlines_set", bool(comp.stage_1_deadline and comp.stage_2_deadline), "stage_1_deadline / stage_2_deadline"))
        if comp.stage_1_deadline and comp.stage_2_deadline:
            out.append(_c("deadlines_ordered", comp.stage_1_deadline < comp.stage_2_deadline, "stage 1 before stage 2"))
    for stage, keys in ((1, STAGE1_WEIGHT_KEYS), (2, STAGE2_WEIGHT_KEYS)):
        r = db.query(RubricVersion).filter(RubricVersion.stage == stage).order_by(RubricVersion.created_at.desc()).first()
        out.append(_c(f"rubric_stage{stage}_locked", bool(r and r.is_locked), "latest rubric locked"))
        out.append(_c(f"rubric_stage{stage}_weights_sum_to_1", bool(r and weights_sum_ok(r.rubric_json or {}, keys)), "weights sum to 1.0"))
    return out
