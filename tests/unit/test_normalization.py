import pytest
from mailcerto.core.normalization import detect_and_normalize_target

def test_detect_and_normalize_domain():
    normalized, t_type = detect_and_normalize_target("  SendLite.app  ")
    assert normalized == "sendlite.app"
    assert t_type == "domain"

def test_detect_and_normalize_ip():
    normalized, t_type = detect_and_normalize_target("1.1.1.1")
    assert normalized == "1.1.1.1"
    assert t_type == "ip"

def test_detect_and_normalize_url():
    normalized, t_type = detect_and_normalize_target("https://sendlite.app/path?query=1")
    assert normalized == "https://sendlite.app/path?query=1"
    assert t_type == "url"

def test_detect_and_normalize_email():
    normalized, t_type = detect_and_normalize_target("test@domain.com")
    assert normalized == "test@domain.com"
    assert t_type == "email"

def test_detect_and_normalize_invalid():
    normalized, t_type = detect_and_normalize_target("not-a-valid-target!!!")
    assert t_type == "invalid"
