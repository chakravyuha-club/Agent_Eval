import pytest
import pandas as pd
from evaluator.stage1.evaluator import validate_prediction_file, evaluate_stage1_submission

def test_validate_prediction_file_valid_csv():
    csv_content = b"task_id,predicted_label,selected_tool\npriv_001,label_a,tool_a\npriv_002,label_b,tool_b\n"
    is_valid, err, df = validate_prediction_file(csv_content, "submission.csv")
    assert is_valid is True
    assert err is None
    assert len(df) == 2

def test_validate_prediction_file_missing_required_column():
    csv_content = b"random_id,predicted_label\n1,label_a\n"
    is_valid, err, df = validate_prediction_file(csv_content, "submission.csv")
    assert is_valid is False
    assert "Missing required columns" in err

def test_validate_prediction_file_duplicate_task_ids():
    csv_content = b"task_id,predicted_label\npriv_001,label_a\npriv_001,label_b\n"
    is_valid, err, df = validate_prediction_file(csv_content, "submission.csv")
    assert is_valid is False
    assert "Duplicate task_id" in err

def test_evaluate_stage1_submission_scoring():
    sub_df = pd.DataFrame([
        {"task_id": "t1", "predicted_label": "cat", "selected_tool": "tool1"},
        {"task_id": "t2", "predicted_label": "dog", "selected_tool": "tool2"}
    ])
    gt_df = pd.DataFrame([
        {"task_id": "t1", "target_label": "cat", "required_tool": "tool1"},
        {"task_id": "t2", "target_label": "dog", "required_tool": "tool2"}
    ])
    rubric = {
        "weight_accuracy": 0.40,
        "weight_tool": 0.20,
        "weight_constraint": 0.15,
        "weight_quality": 0.15,
        "weight_efficiency": 0.10
    }
    res = evaluate_stage1_submission(sub_df, gt_df, rubric)
    assert res["task_success_rate"] == 100.0
    assert res["total_score"] > 90.0
    assert len(res["task_results"]) == 2
