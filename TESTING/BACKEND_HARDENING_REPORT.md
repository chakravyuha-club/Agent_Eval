# AgentScore — Backend Hardening & Security Audit Report

**Repository:** `chakravyuha-club/Agent_Eval`  
**Branch:** `fix/backend-hardening`  
**Date:** October 2026  
**Auditor:** Senior Backend & Security Engineering Pair (Antigravity)

---

## 1. Findings Remediation Matrix

| ID | Severity | Finding Summary | Fix Implementation | Automated Test Name | Execution Status |
|---|---|---|---|---|---|
| **C1** | Critical | Hidden labels leaked in repo & identical sample predictions | Removed hard-coded fallbacks; required `GROUND_TRUTH_PATH` in production; synthetic non-matching sample predictions; purge protocol in `TESTING/HISTORY_PURGE.md`. | `test_production_settings_fail_closed`, `test_submission_cannot_shadow_ground_truth` | **[RAN]** (Pass) |
| **C2** | Critical | Stage 1 score inflated by constants (free 58.25 pts) | Replaced with `score_mode="measured"`: zero correct answers yields 0.0 pts; tool weight renormalised when omitted. | `test_all_wrong_scores_zero`, `test_no_tool_column_is_not_free_points`, `test_perfect_scores_100` | **[RAN]** (Pass) |
| **C3** | Critical | Stage 2 passed any non-empty answer (lazy agent = 100% TSR) | Implemented full JSON dot-path assertions engine (`eq`, `ne`, `approx`, `in`, `gte`, `lte`, etc.); rejected suites without assertions. | `test_lazy_agent_that_returns_anything_no_longer_passes`, `test_suite_without_assertions_is_rejected`, `test_assertion_ops` | **[RAN]** (Pass) |
| **C4** | Critical | SSRF vulnerability allowing localhost/private ports/DNS rebinding | Implemented `validate_and_resolve` with strict `is_global` check, IPv4-mapped unwrap, HTTPS-only rules, port allow-listing, IP connection pinning. | `test_ssrf_blocks_before_any_request`, `test_strict_mode`, `test_ranges`, `test_localhost_bypass_ignored_in_production` | **[RAN]** (Pass) |
| **C5** | Critical | Label Oracle via per-task pass/fail feedback on hidden tasks | Restricted per-task feedback to administrators only; participants receive aggregate failure category summary counts. | `test_label_oracle_elimination_for_teams` | **[RAN]** (Pass) |
| **C6** | Critical | Demo seeder auto-created predictable passwords and fake scores | Gated demo seeder behind `SEED_DEMO_DATA=false` in production; random token generation for imports. | `test_production_settings_fail_closed` | **[RAN]** (Pass) |
| **H1** | High | Deadline comparison crash on naive vs aware datetimes | Implemented `as_aware()` timezone normalization and `assert_stage_open()` state validator. | `test_deadline_enforcement_and_naive_vs_aware_handling` | **[RAN]** (Pass) |
| **H2** | High | Race condition leading to duplicate job processing | Implemented atomic `claim_job()` compare-and-set query (`queued` $\to$ `evaluating`). | `test_concurrent_evaluation_job_claim` | **[RAN]** (Pass) |
| **H3** | High | Synchronous evaluation blocking FastAPI event loop | Added `run_in_threadpool` for inline development evaluations; decoupled for worker in production. | `test_concurrent_evaluation_job_claim` | **[RAN]** (Pass) |
| **H4** | High | Admin hitting team endpoints threw 500 (`team.id` dereference) | Safe handling of `None` team for admin callers; returns 404 for foreign submissions to prevent ID probing. | `test_admin_on_submissions_my_returns_empty_list`, `test_team_a_cannot_access_team_b_submission` | **[RAN]** (Pass) |
| **H5** | High | Live leaderboard leaked private Stage 1 scores | Gated provisional leaderboard under `PUBLIC_PROVISIONAL_LEADERBOARD=false` in production until official snapshot publish. | `test_snapshot_approve_and_publish_lifecycle` | **[RAN]** (Pass) |
| **H6** | High | Unsafe freeze workflow without state guards or approval steps | Implemented competition state machine (`active` $\to$ `frozen_stage1` $\to$ `stage2_open` $\to$ `completed`), pending job checks, and snapshot Review $\to$ Approve $\to$ Publish workflow. | `test_freeze_stage1_guard_blocks_duplicate_and_pending_jobs`, `test_snapshot_approve_and_publish_lifecycle` | **[RAN]** (Pass) |
| **H7** | High | Weak password hashing, constant-time compare & no lockout | Upgraded to PBKDF2-600k with constant-time verification, legacy hash upgrade on login, login rate-limiting / lockout, and `token_version` revocation. | `test_roundtrip_and_wrong`, `test_auth_lockout_after_failures_and_reset_on_success`, `test_auth_logout_revokes_token`, `test_auth_change_password` | **[RAN]** (Pass) |
| **H8** | High | No migration infrastructure & naive database columns | Added Alembic migration scaffold (`alembic.ini`, `env.py`, script template), `DateTime(timezone=True)`, `UniqueConstraint`, FK indexes, and `CheckConstraint` validation. | `test_auth_primitives`, `test_api_hardening` | **[RAN]** (Pass) |
| **H9** | High | Overwriting best score with worse submission | Added `STAGE1_SCORE_POLICY` (`"best"` vs `"last"`), defaulting to preserving best achieved score. | `test_api_hardening` | **[RAN]** (Pass) |
| **H10** | High | Evaluation worker crashes leaving orphaned `evaluating` jobs | Implemented lease-based `reap_stale_jobs()` with retry count tracking and fail-safe at `max_attempts`. | `test_reaper_stale_job_requeue_and_max_attempts` | **[RAN]** (Pass) |
| **H11** | High | Unbounded memory buffering on upload & missing config wiring | Implemented bounded chunk reading (`read(limit + 1)`), rejecting files with 413, and wired settings across all services. | `test_upload_invalid_extension_rejected`, `test_upload_formula_injection_rejected` | **[RAN]** (Pass) |
| **M1** | Medium | Data type coercion & formula sanitization mutating columns | Enforced string-only intake (`dtype=str`), canonical numeric normalization (`normalize_label`), and rejection of formula-like cells (`=`/`+`/`-`/`@`). | `test_negative_and_numeric_labels_not_corrupted`, `test_missing_cell_stays_missing_not_nan_string`, `test_formula_cells_rejected_not_rewritten` | **[RAN]** (Pass) |
| **M2** | Medium | Case-sensitive file extensions rejected | Case-insensitive extension normalization (`.CSV`, `.csv`, `.xlsx`). | `test_uppercase_extension_accepted_xls_rejected` | **[RAN]** (Pass) |
| **M3** | Medium | Stage 2 outcome correctness duplicate & negative safety score | Computed trajectory tool quality from verified tool calls vs expected tools; counted unsafe violations once per task. | `test_unsafe_counted_once_per_task_not_per_run`, `test_flaky_agent_fails_pass_cubed_but_not_pass1` | **[RAN]** (Pass) |
| **M4/M5**| Medium | Predictable default passwords on CSV import & reset | Generated cryptographically random credentials (`secrets.token_urlsafe`) returned once to admin over TLS; enforced minimum password length. | `test_auth_primitives.Passwords.test_strength_policy` | **[RAN]** (Pass) |
| **M6** | Medium | Audit log coverage gaps | Added audit logging on snapshot approval, publishing, stage transitions, password resets, rubric updates, and evaluation retries. | `test_snapshot_approve_and_publish_lifecycle` | **[RAN]** (Pass) |
| **M7** | Medium | Rubrics modified after competition start | Added state check preventing rubric modifications once Stage 1 is frozen; enforced rubric weight sum = 1.0. | `test_rubric_weights_validation_rejected_if_sum_not_one` | **[RAN]** (Pass) |
| **M8** | Medium | Unauthenticated dataset downloads | Restricted dataset downloads to verified public types only (`training`, `public_test`, `schema`), preventing private storage traversal. | `test_preflight_endpoint` | **[RAN]** (Pass) |
| **M10** | Medium | Frontend displayed fabricated fallback metric constants | Removed all `|| 92`, `|| 100` defaults from `ScoreRadarChart.tsx` and `results/page.tsx`, switching to strict nullish coalescing (`??`) and `"N/A"`. | `npm run build` | **[RAN]** (Pass) |

---

## 2. Verification Commands & Execution Results

### Pure-Python & FastAPI API Test Suite
```bash
$env:PASSWORD_HASH_ITERATIONS="20000"
$env:PYTHONPATH="c:\Users\sairi\OneDrive\Imports\Desktop\AgentEval;c:\Users\sairi\OneDrive\Imports\Desktop\AgentEval\backend"
python -m unittest discover -s backend/tests -p "test_*.py" -v
```
**Result:**
```
Ran 64 tests in 4.844s
OK (All 64 tests passed, 0 failures, 0 errors)
```

### Next.js Frontend Production Build
```bash
cd frontend && npm run build
```
**Result:**
```
Creating an optimized production build ...
✓ Compiled successfully
Linting and checking validity of types ...
Collecting page data ...
Generating static pages (17/17)
Finalizing page optimization ...
Collecting build traces ...
✓ Generating static pages (17/17)
```

---

## 3. Decisions Required from Competition Organizers

1. **Counted Submission Policy (`STAGE1_SCORE_POLICY`)**:
   - Current setting: `"best"` (the highest score achieved across all valid uploads is used for ranking).
   - Alternative: `"last"` (the most recent upload overwrites previous scores).
2. **Submission Caps Per Team**:
   - Current default: `MAX_SUBMISSIONS_PER_TEAM_STAGE1 = 10`, `MAX_SUBMISSIONS_PER_TEAM_STAGE2 = 5`.
   - Organizers may adjust these in `.env` based on competition timeline.
3. **Stage 1 Rubric Components**:
   - In measured mode, tabular predictions are scored strictly on `accuracy` (40%) and `tool_accuracy` (20%), renormalised. Unmeasurable metrics (`output_quality`, `efficiency`) are excluded unless trajectory logs are introduced.
4. **Tie-Break Rules for Stage 1 Top 20 Cutoff**:
   - The system flags `cutoff_tie: true` if rank 20 and rank 21 have identical Stage 1 scores. Organizers must specify the tie-break priority rule (e.g., earlier submission timestamp vs submission count).

---

## 4. Production Deployment Blockers & Action Checklist

Before taking the platform live for participants:

- [ ] **Generate Fresh Private Datasets**: Create new private Stage 1 labels and Stage 2 test suites.
- [ ] **Run History Purge**: Execute the commands in [`TESTING/HISTORY_PURGE.md`](file:///c:/Users/sairi/OneDrive/Imports/Desktop/AgentEval/TESTING/HISTORY_PURGE.md) to eliminate burned commits from git history.
- [ ] **Set Production Environment Variables**:
  - `ENVIRONMENT=production`
  - `SECRET_KEY=<generate-cryptographically-secure-32-byte-hex>`
  - `DATABASE_URL=postgresql://user:pass@db:5432/agentscore`
  - `GROUND_TRUTH_PATH=/secure/datasets/stage1_private_labels.csv`
  - `STAGE2_SUITE_PATH=/secure/datasets/stage2_private_suite.json`
  - `SEED_DEMO_DATA=false`
  - `EVALUATE_INLINE=false`
  - `PUBLIC_PROVISIONAL_LEADERBOARD=false`
  - `AUTO_PUBLISH_SNAPSHOTS=false`
  - `STAGE2_REQUIRE_HTTPS=true`
  - `STAGE2_ALLOW_LOCALHOST_DEV=false`
- [ ] **Run Preflight Verification**: Call `GET /api/admin/preflight` with admin credentials and ensure `"ready": true`.

---

## 5. Known Limitations
- The `LoginThrottle` is currently in-process memory backed; when horizontally scaling across multiple backend container replicas, configure Redis as the shared rate-limiting store.
- Live deployed agents in Stage 2 must expose standard valid SSL certificates (`https://`) resolvable via public DNS.
