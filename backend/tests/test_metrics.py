import pytest
from evaluator.metrics.metrics import (
    calculate_task_success_rate,
    calculate_pass_at_1,
    calculate_pass_cubed,
    calculate_safety_score,
    calculate_latency_percentiles,
    calculate_classification_metrics,
    normalize_efficiency_score
)

def test_task_success_rate():
    assert calculate_task_success_rate(8, 10) == 80.0
    assert calculate_task_success_rate(0, 10) == 0.0
    assert calculate_task_success_rate(10, 10) == 100.0
    assert calculate_task_success_rate(0, 0) == 0.0

def test_pass_at_1_and_pass_cubed():
    # 7 succeeded on first run out of 10
    assert calculate_pass_at_1(7, 10) == 70.0
    # 5 succeeded on all 3 consecutive runs out of 10
    assert calculate_pass_cubed(5, 10) == 50.0

def test_safety_score():
    # 1 unsafe action out of 5 adversarial probes -> 100 * (1 - 1/5) = 80%
    assert calculate_safety_score(1, 5) == 80.0
    # 0 unsafe actions out of 4 probes -> 100%
    assert calculate_safety_score(0, 4) == 100.0
    # 0 adversarial tests -> returns None (unavailable, not fake 100)
    assert calculate_safety_score(0, 0) is None

def test_latency_percentiles():
    latencies = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
    stats = calculate_latency_percentiles(latencies)
    assert stats["p50"] == 55.0
    assert stats["min"] == 10.0
    assert stats["max"] == 100.0

def test_classification_metrics():
    y_true = ["cat", "dog", "cat", "bird"]
    y_pred = ["cat", "dog", "dog", "bird"]
    metrics = calculate_classification_metrics(y_true, y_pred)
    assert metrics["accuracy"] == 75.0
    assert metrics["macro_f1"] > 0.0

def test_normalize_efficiency_score():
    assert normalize_efficiency_score(150.0, target_ms=200.0) == 100.0
    assert normalize_efficiency_score(3500.0, max_ms=3000.0) == 0.0
    score = normalize_efficiency_score(1600.0, target_ms=200.0, max_ms=3000.0)
    assert 40.0 <= score <= 60.0
