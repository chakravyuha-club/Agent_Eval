import pytest
from evaluator.safety.ssrf_validator import validate_target_url, is_ip_prohibited

def test_prohibited_ips():
    assert is_ip_prohibited("127.0.0.1") is True
    assert is_ip_prohibited("10.0.0.1") is True
    assert is_ip_prohibited("172.16.0.5") is True
    assert is_ip_prohibited("192.168.1.1") is True
    assert is_ip_prohibited("169.254.169.254") is True # AWS/GCP Metadata
    assert is_ip_prohibited("::1") is True # IPv6 loopback
    # Public IP
    assert is_ip_prohibited("8.8.8.8") is False
    assert is_ip_prohibited("1.1.1.1") is False

def test_url_validation_blocks_localhost_by_default():
    is_valid, err = validate_target_url("http://127.0.0.1:8000/predict", allow_localhost_for_testing=False)
    assert is_valid is False
    assert "Forbidden target host" in err

def test_url_validation_accepts_valid_http_scheme():
    is_valid, err = validate_target_url("http://127.0.0.1:8000/predict", allow_localhost_for_testing=True)
    assert is_valid is True
    assert err is None

def test_url_validation_rejects_invalid_scheme():
    is_valid, err = validate_target_url("ftp://agent.example.com/predict")
    assert is_valid is False
    assert "Only 'http' and 'https'" in err
