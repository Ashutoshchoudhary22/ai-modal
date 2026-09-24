"""Browser URL and policy tests."""

import pytest
from agent.browser.errors import BrowserError
from agent.browser.policy import validate_url
from ai_platform_protocol.browser import BrowserErrorCode


def test_valid_https_url():
    assert validate_url("https://example.com/path") == "https://example.com/path"


def test_rejects_file_scheme():
    with pytest.raises(BrowserError) as exc:
        validate_url("file:///etc/passwd")
    assert exc.value.code == BrowserErrorCode.UNSAFE_URL


def test_rejects_javascript_scheme():
    with pytest.raises(BrowserError) as exc:
        validate_url("javascript:alert(1)")
    assert exc.value.code == BrowserErrorCode.UNSAFE_URL


def test_rejects_data_scheme():
    with pytest.raises(BrowserError) as exc:
        validate_url("data:text/html,<script>alert(1)</script>")
    assert exc.value.code == BrowserErrorCode.UNSAFE_URL


def test_domain_allowlist():
    with pytest.raises(BrowserError) as exc:
        validate_url("https://evil.example", allowed_domains=["example.com"])
    assert exc.value.code == BrowserErrorCode.DOMAIN_NOT_ALLOWED


def test_domain_allowlist_match():
    assert (
        validate_url("https://app.example.com", allowed_domains=["example.com"])
        == "https://app.example.com"
    )


def test_blocked_domain():
    with pytest.raises(BrowserError) as exc:
        validate_url("https://blocked.example", blocked_domains=["blocked.example"])
    assert exc.value.code == BrowserErrorCode.DOMAIN_NOT_ALLOWED


def test_ssrf_metadata_endpoint():
    with pytest.raises(BrowserError) as exc:
        validate_url("http://169.254.169.254/latest/meta-data/")
    assert exc.value.code == BrowserErrorCode.SSRF_BLOCKED


def test_ssrf_private_ip():
    with pytest.raises(BrowserError) as exc:
        validate_url("http://192.168.1.1/admin")
    assert exc.value.code == BrowserErrorCode.SSRF_BLOCKED


def test_localhost_allowed_in_dev():
    assert validate_url("http://localhost:3000", allow_localhost=True) == "http://localhost:3000"


def test_localhost_blocked_when_disabled():
    with pytest.raises(BrowserError) as exc:
        validate_url("http://127.0.0.1:3000", allow_localhost=False)
    assert exc.value.code == BrowserErrorCode.SSRF_BLOCKED
