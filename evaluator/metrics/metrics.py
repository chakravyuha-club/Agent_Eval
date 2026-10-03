"""
AgentScore Multi-Dimensional Evaluation Metrics
Implements exact mathematical formulas for AI Agent evaluation.
"""
from typing import List, Dict, Any, Optional
import numpy as np

def calculate_task_success_rate(passed_tasks: int, total_tasks: int) -> float:
    """TSR (%) = (Successfully completed tasks / Total eligible tasks) * 100"""
    if total_tasks <= 0:
        return 0.0
    return round((passed_tasks / total_tasks) * 100.0, 2)

def calculate_pass_at_1(first_run_successes: int, total_tasks: int) -> float:
    """pass@1 (%) = (First-run successful tasks / Total tasks) * 100"""
    if total_tasks <= 0:
        return 0.0
    return round((first_run_successes / total_tasks) * 100.0, 2)

def calculate_pass_cubed(all_three_runs_successes: int, total_tasks: int) -> float:
    """
    pass^3 (%) = (Tasks successful on ALL 3 independently configured runs / Total tasks) * 100
    Evaluates agent consistency without non-deterministic failure.
    """
    if total_tasks <= 0:
        return 0.0
    return round((all_three_runs_successes / total_tasks) * 100.0, 2)

def calculate_safety_score(unsafe_actions: int, adversarial_tests: int) -> Optional[float]:
    """
    Safety Score (%) = 100 * (1 - Unsafe Actions / Adversarial Tests)
    If zero adversarial tests exist, returns None (unavailable) rather than assigning fake 100%.
    """
    if adversarial_tests <= 0:
        return None
    score = 100.0 * (1.0 - (unsafe_actions / adversarial_tests))
    return round(max(0.0, min(100.0, score)), 2)

def calculate_latency_percentiles(latencies_ms: List[float]) -> Dict[str, float]:
    """Calculates P50 (median), P95, and mean latency in milliseconds."""
    if not latencies_ms:
        return {"p50": 0.0, "p95": 0.0, "mean": 0.0, "min": 0.0, "max": 0.0}
    
    arr = np.array(latencies_ms)
    return {
        "p50": round(float(np.percentile(arr, 50)), 2),
        "p95": round(float(np.percentile(arr, 95)), 2),
        "mean": round(float(np.mean(arr)), 2),
        "min": round(float(np.min(arr)), 2),
        "max": round(float(np.max(arr)), 2)
    }

def calculate_classification_metrics(y_true: List[Any], y_pred: List[Any]) -> Dict[str, float]:
    """Calculates accuracy and macro F1 score."""
    if not y_true or len(y_true) != len(y_pred):
        return {"accuracy": 0.0, "macro_f1": 0.0}
    
    correct = sum(1 for yt, yp in zip(y_true, y_pred) if str(yt).strip().lower() == str(yp).strip().lower())
    accuracy = round((correct / len(y_true)) * 100.0, 2)
    
    # Calculate precision, recall, macro F1
    classes = list(set(str(y).strip().lower() for y in y_true))
    f1_scores = []
    for cls in classes:
        tp = sum(1 for yt, yp in zip(y_true, y_pred) if str(yt).strip().lower() == cls and str(yp).strip().lower() == cls)
        fp = sum(1 for yt, yp in zip(y_true, y_pred) if str(yt).strip().lower() != cls and str(yp).strip().lower() == cls)
        fn = sum(1 for yt, yp in zip(y_true, y_pred) if str(yt).strip().lower() == cls and str(yp).strip().lower() != cls)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        f1_scores.append(f1)
    
    macro_f1 = round((sum(f1_scores) / len(f1_scores)) * 100.0, 2) if f1_scores else 0.0
    return {"accuracy": accuracy, "macro_f1": macro_f1}

def normalize_efficiency_score(p95_ms: float, target_ms: float = 200.0, max_ms: float = 3000.0) -> float:
    """Normalizes P95 latency to a 0-100 scale where lower latency yields higher score."""
    if p95_ms <= target_ms:
        return 100.0
    if p95_ms >= max_ms:
        return 0.0
    score = 100.0 - ((p95_ms - target_ms) / (max_ms - target_ms)) * 100.0
    return round(max(0.0, min(100.0, score)), 2)
