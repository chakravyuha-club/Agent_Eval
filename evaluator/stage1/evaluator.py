"""
Stage 1 File Evaluation Engine (hardened).

Fixes vs. original (each is covered by tests in backend/tests/test_evaluator_hardening.py):
  * All cells are read as TEXT (dtype=str) - pandas no longer turns "-1" into -1.0 or "007" into 7.
  * Formula-like cells are REJECTED instead of silently rewritten (the old lstrip mutated
    whole columns and turned missing values into the string "nan").
  * Extension check is case-insensitive; .xls is rejected (needs xlrd, not a dependency).
  * Row cap, xlsx zip-bomb / macro guard, strict UTF-8, unknown/missing task_id policy.
  * Scoring no longer awards points for constants (quality=95, efficiency=90, tool=100 when
    no tool column). Default `score_mode="measured"` scores ONLY what is measurable and
    renormalises weights. `score_mode="legacy"` reproduces the old formula for comparison.
"""
import io
import re
import zipfile
from decimal import Decimal, InvalidOperation
from typing import Any, Collection, Dict, List, Optional, Tuple

import pandas as pd

from evaluator.metrics.metrics import calculate_classification_metrics, calculate_task_success_rate

REQUIRED_COLUMNS = ["task_id", "predicted_label"]
MAX_ROWS_DEFAULT = 10_000
MAX_XLSX_UNCOMPRESSED_BYTES = 100 * 1024 * 1024
_NUMERIC_RE = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$")
_FORMULA_START = ("=", "+", "-", "@", "\t", "\r")


def _is_formula_like(raw: str) -> bool:
    """Spreadsheet-formula heuristics on the RAW cell (no stripping, so a leading TAB is caught)."""
    if not raw or raw[0] not in _FORMULA_START:
        return False
    return not _NUMERIC_RE.match(raw.strip())  # "-1" / "+5" are legitimate numeric labels


def normalize_label(value: Any) -> str:
    """Canonical comparison form: trimmed, case-folded, numerics canonicalised ('6' == '6.0')."""
    s = "" if value is None else str(value).strip()
    if s and _NUMERIC_RE.match(s):
        try:
            d = Decimal(s).normalize()
            return format(d, "f") if d == d.to_integral() or abs(d) < Decimal("1e15") else s
        except InvalidOperation:
            pass
    return s.casefold()


def _read_table(file_bytes: bytes, filename: str, max_rows: int) -> pd.DataFrame:
    name = (filename or "").lower()
    if name.endswith(".csv"):
        try:
            text = file_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise ValueError("CSV must be UTF-8 encoded.")
        return pd.read_csv(io.StringIO(text), dtype=str, keep_default_na=False, nrows=max_rows + 1)
    if name.endswith(".xlsx"):
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
                infos = zf.infolist()
                if sum(i.file_size for i in infos) > MAX_XLSX_UNCOMPRESSED_BYTES:
                    raise ValueError("Workbook expands beyond the allowed size.")
                if any(i.filename.lower().endswith("vbaproject.bin") for i in infos):
                    raise ValueError("Macro-enabled workbooks are not accepted.")
        except zipfile.BadZipFile:
            raise ValueError("File is not a valid .xlsx workbook.")
        df = pd.read_excel(io.BytesIO(file_bytes), dtype=str, engine="openpyxl",
                           keep_default_na=False, nrows=max_rows + 1)
        return df.fillna("")
    raise ValueError("Unsupported file format. Only .csv and .xlsx files are accepted.")


def validate_prediction_file(
    file_bytes: bytes,
    filename: str,
    *,
    expected_task_ids: Optional[Collection[str]] = None,
    max_rows: int = MAX_ROWS_DEFAULT,
    require_complete: bool = False,
) -> Tuple[bool, Optional[str], Optional[pd.DataFrame]]:
    """
    Validate a CSV/XLSX prediction file. Returns (is_valid, error_message, dataframe).

    If `expected_task_ids` is supplied (server-side only!) the file must not contain unknown ids,
    and with `require_complete=True` must contain every expected id. Error messages report COUNTS
    only, never the hidden ids.
    """
    try:
        df = _read_table(file_bytes, filename, max_rows)
    except ValueError as e:
        return False, str(e), None
    except Exception:
        return False, "Failed to parse spreadsheet file.", None

    if df.empty:
        return False, "Submission file is empty.", None
    if len(df) > max_rows:
        return False, f"Submission has more than {max_rows} rows.", None

    cols = [str(c).strip().lower() for c in df.columns]
    if len(set(cols)) != len(cols):
        return False, "Duplicate column names detected.", None
    df.columns = cols

    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        return False, f"Missing required columns in submission: {missing_cols}. Found: {list(df.columns)}", None

    for c in df.columns:
        df[c] = df[c].astype(str).str.replace("\x00", "", regex=False)
    bad_cells = sum(_is_formula_like(v) for c in df.columns for v in df[c])
    if bad_cells:
        return False, f"{bad_cells} cell(s) look like spreadsheet formulas (start with = + - @). Remove them and resubmit.", None
    for c in df.columns:
        df[c] = df[c].str.strip()

    if (df["task_id"] == "").any():
        return False, "Rows with an empty task_id are not allowed.", None
    if df["task_id"].duplicated().any():
        dups = df[df["task_id"].duplicated()]["task_id"].tolist()[:5]
        return False, f"Duplicate task_id entries detected in submission: {dups}", None

    if expected_task_ids is not None:
        expected = set(map(str, expected_task_ids))
        ids = set(df["task_id"])
        unknown = len(ids - expected)
        if unknown:
            return False, f"{unknown} row(s) have a task_id that is not part of this competition.", None
        if require_complete:
            absent = len(expected - ids)
            if absent:
                return False, f"{absent} expected task_id(s) are missing from the submission.", None
            empty = int((df["predicted_label"] == "").sum())
            if empty:
                return False, f"{empty} row(s) have an empty predicted_label.", None

    return True, None, df


def _weighted(components: Dict[str, Tuple[Optional[float], float]]) -> Tuple[float, List[str]]:
    used = {k: (v, w) for k, (v, w) in components.items() if v is not None and w > 0}
    total_w = sum(w for _, w in used.values())
    if total_w <= 0:
        return 0.0, []
    return round(sum(v * w for v, w in used.values()) / total_w, 2), sorted(used)


def evaluate_stage1_submission(
    submission_df: pd.DataFrame,
    ground_truth_df: pd.DataFrame,
    rubric: Dict[str, Any],
) -> Dict[str, Any]:
    """Score predictions against the hidden ground truth. Never returns hidden labels."""
    gt = ground_truth_df.copy()
    gt.columns = [str(c).strip().lower() for c in gt.columns]
    gt["task_id"] = gt["task_id"].astype(str).str.strip()
    sub = submission_df.copy()
    sub.columns = [str(c).strip().lower() for c in sub.columns]
    sub["task_id"] = sub["task_id"].astype(str).str.strip()
    # Never let a submission column shadow ground-truth columns.
    sub = sub[[c for c in sub.columns if c in ("task_id", "predicted_label", "selected_tool")]]

    merged = pd.merge(gt, sub, on="task_id", how="left", suffixes=("", "_sub"))
    total = len(gt)
    has_tool_cols = "required_tool" in merged.columns and "selected_tool" in merged.columns

    y_true, y_pred, task_results = [], [], []
    passed = tool_ok = tool_n = answered = 0
    for _, row in merged.iterrows():
        t = normalize_label(row.get("target_label"))
        raw_pred = row.get("predicted_label")
        p = "" if pd.isna(raw_pred) else normalize_label(raw_pred)
        ok = bool(p) and p == t
        passed += ok
        answered += bool(p)
        y_true.append(t)
        y_pred.append(p)
        if has_tool_cols and not pd.isna(row.get("required_tool")) and str(row["required_tool"]).strip():
            tool_n += 1
            sel = row.get("selected_tool")
            tool_ok += (not pd.isna(sel)) and normalize_label(sel) == normalize_label(row["required_tool"])
        task_results.append({
            "task_id": row["task_id"], "passed": ok, "latency_ms": 0.0,
            "error_category": None if ok else ("missing_prediction" if not p else "incorrect_label"),
        })

    tsr = calculate_task_success_rate(passed, total)
    cls = calculate_classification_metrics(y_true, y_pred)
    accuracy, macro_f1 = cls["accuracy"], cls["macro_f1"]
    tool_acc = round(tool_ok / tool_n * 100.0, 2) if tool_n else None
    completeness = round(answered / total * 100.0, 2) if total else 0.0

    w_acc = rubric.get("weight_accuracy", 0.40)
    w_tool = rubric.get("weight_tool", 0.20)
    mode = rubric.get("score_mode", "measured")

    if mode == "legacy":  # reproduces the original constants, for regression comparison only
        quality = 95.0 if answered == total else 80.0
        eff = 90.0
        total_score, used = _weighted({
            "accuracy": (accuracy, w_acc), "tool_accuracy": (tool_acc if tool_acc is not None else 100.0, w_tool),
            "constraint_compliance": (completeness, rubric.get("weight_constraint", 0.15)),
            "output_quality": (quality, rubric.get("weight_quality", 0.15)),
            "efficiency": (eff, rubric.get("weight_efficiency", 0.10)),
        })
        quality_v, eff_v = quality, eff
    else:  # measured: only correctness components that actually exist for a prediction file
        total_score, used = _weighted({"accuracy": (accuracy, w_acc), "tool_accuracy": (tool_acc, w_tool)})
        quality_v = eff_v = None

    return {
        "stage": 1,
        "score_mode": mode,
        "components_used": used,
        "total_score": total_score,
        "task_success_rate": tsr,
        "passed_tasks": passed,
        "total_tasks": total,
        "metrics": {
            "accuracy": accuracy, "macro_f1": macro_f1, "tool_accuracy": tool_acc,
            "constraint_compliance": completeness,  # informational: share of tasks answered
            "output_quality": quality_v, "efficiency": eff_v,
        },
        "score_breakdown": {
            "accuracy_weighted": round(accuracy * w_acc, 2),
            "tool_weighted": round((tool_acc or 0.0) * w_tool, 2),
        },
        "task_results": task_results,  # INTERNAL ONLY - never return per-task pass/fail to teams
    }
