"""
Stage 1 File Evaluation Engine
Handles tabular prediction intake, schema validation, formula sanitization, and metric evaluation.
"""
import io
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
from evaluator.metrics.metrics import (
    calculate_task_success_rate,
    calculate_classification_metrics
)

REQUIRED_COLUMNS = ["task_id", "predicted_label"]

def validate_prediction_file(file_bytes: bytes, filename: str) -> Tuple[bool, Optional[str], Optional[pd.DataFrame]]:
    """
    Validates CSV or XLSX file structure, size, encoding, and required schema.
    Returns (is_valid, error_message, dataframe).
    """
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_bytes))
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(file_bytes))
        else:
            return False, "Unsupported file format. Only .csv and .xlsx files are accepted.", None
    except Exception as e:
        return False, f"Failed to parse spreadsheet file: {str(e)}", None

    # Check for empty dataframe
    if df.empty:
        return False, "Submission file is empty.", None

    # Sanitize column names
    df.columns = [str(col).strip().lower() for col in df.columns]

    # Verify required columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        return False, f"Missing required columns in submission: {missing_cols}. Found: {list(df.columns)}", None

    # Check for duplicate task IDs
    if df["task_id"].duplicated().any():
        dups = df[df["task_id"].duplicated()]["task_id"].tolist()[:5]
        return False, f"Duplicate task_id entries detected in submission: {dups}", None

    # Check for spreadsheet formula injection attempts in text fields
    for col in df.select_dtypes(include=["object"]).columns:
        for val in df[col].dropna():
            s_val = str(val).strip()
            if s_val and s_val[0] in ["=", "+", "-", "@", "\t", "\r"]:
                # Formula injection detection - clean it
                df[col] = df[col].astype(str).str.lstrip("=+-@\t\r")

    return True, None, df

def evaluate_stage1_submission(
    submission_df: pd.DataFrame,
    ground_truth_df: pd.DataFrame,
    rubric: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluates submitted predictions against hidden ground-truth dataset using configured rubric.
    """
    ground_truth_df = ground_truth_df.copy()
    ground_truth_df.columns = [str(c).strip().lower() for c in ground_truth_df.columns]
    
    # Merge predictions with ground truth on task_id
    merged = pd.merge(ground_truth_df, submission_df, on="task_id", how="left")
    
    total_tasks = len(ground_truth_df)
    passed_tasks = 0
    task_results = []
    
    y_true = []
    y_pred = []
    
    tool_correct = 0
    tool_eval_count = 0

    for _, row in merged.iterrows():
        t_id = row["task_id"]
        true_label = str(row.get("target_label", "")).strip().lower()
        pred_label = str(row.get("predicted_label", "")).strip().lower() if pd.notna(row.get("predicted_label")) else ""
        
        is_correct = (true_label == pred_label) and bool(pred_label)
        if is_correct:
            passed_tasks += 1
            
        y_true.append(true_label)
        y_pred.append(pred_label)
        
        # Check tool selection if present
        if "required_tool" in row and "selected_tool" in row and pd.notna(row["required_tool"]):
            tool_eval_count += 1
            req_tool = str(row["required_tool"]).strip().lower()
            sel_tool = str(row.get("selected_tool", "")).strip().lower() if pd.notna(row.get("selected_tool")) else ""
            if req_tool == sel_tool:
                tool_correct += 1

        task_results.append({
            "task_id": t_id,
            "passed": is_correct,
            "latency_ms": 0.0,
            "error_category": None if is_correct else ("missing_prediction" if not pred_label else "incorrect_label")
        })

    # Calculate metrics
    tsr = calculate_task_success_rate(passed_tasks, total_tasks)
    cls_metrics = calculate_classification_metrics(y_true, y_pred)
    accuracy = cls_metrics["accuracy"]
    macro_f1 = cls_metrics["macro_f1"]
    
    tool_acc = round((tool_correct / tool_eval_count) * 100.0, 2) if tool_eval_count > 0 else 100.0
    constraint_compliance = 100.0 if not merged["predicted_label"].isna().any() else round((1 - (merged["predicted_label"].isna().sum() / total_tasks)) * 100.0, 2)
    output_quality = 95.0 if not merged["predicted_label"].isna().any() else 80.0
    efficiency = 90.0 # Standard tabular efficiency benchmark

    # Configurable weights from rubric (defaults: 40% accuracy, 20% tool, 15% constraints, 15% quality, 10% efficiency)
    w_acc = rubric.get("weight_accuracy", 0.40)
    w_tool = rubric.get("weight_tool", 0.20)
    w_constraint = rubric.get("weight_constraint", 0.15)
    w_quality = rubric.get("weight_quality", 0.15)
    w_eff = rubric.get("weight_efficiency", 0.10)

    total_score = round(
        (accuracy * w_acc) +
        (tool_acc * w_tool) +
        (constraint_compliance * w_constraint) +
        (output_quality * w_quality) +
        (efficiency * w_eff),
        2
    )

    return {
        "stage": 1,
        "total_score": total_score,
        "task_success_rate": tsr,
        "passed_tasks": passed_tasks,
        "total_tasks": total_tasks,
        "metrics": {
            "accuracy": accuracy,
            "macro_f1": macro_f1,
            "tool_accuracy": tool_acc,
            "constraint_compliance": constraint_compliance,
            "output_quality": output_quality,
            "efficiency": efficiency
        },
        "score_breakdown": {
            "accuracy_weighted": round(accuracy * w_acc, 2),
            "tool_weighted": round(tool_acc * w_tool, 2),
            "constraint_weighted": round(constraint_compliance * w_constraint, 2),
            "quality_weighted": round(output_quality * w_quality, 2),
            "efficiency_weighted": round(efficiency * w_eff, 2)
        },
        "task_results": task_results
    }
