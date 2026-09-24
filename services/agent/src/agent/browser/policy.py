"""Browser URL, domain, and SSRF policy."""

from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlparse

from agent.browser.errors import BrowserError
from ai_platform_protocol.browser import BrowserErrorCode

_BLOCKED_SCHEMES = {"file", "javascript", "data", "vbscript", "about"}
_METADATA_HOSTS = {
    "169.254.169.254",
    "metadata.google.internal",
    "metadata.google",
}


def validate_url(
    url: str,
    *,
    allowed_domains: list[str] | None = None,
    blocked_domains: list[str] | None = None,
    allow_localhost: bool = True,
) -> str:
    parsed = urlparse(url.strip())
    scheme = (parsed.scheme or "").lower()
    if scheme not in {"http", "https"}:
        raise BrowserError(
            BrowserErrorCode.UNSAFE_URL,
            f"URL scheme '{scheme or 'missing'}' is not allowed",
        )
    host = (parsed.hostname or "").lower()
    if not host:
        raise BrowserError(BrowserErrorCode.UNSAFE_URL, "URL hostname is required")

    if host in _METADATA_HOSTS:
        raise BrowserError(BrowserErrorCode.SSRF_BLOCKED, f"Blocked host: {host}")

    if _is_localhost(host):
        if not allow_localhost:
            raise BrowserError(BrowserErrorCode.SSRF_BLOCKED, "Localhost navigation is disabled")
        return url

    if _is_private_ip(host):
        raise BrowserError(BrowserErrorCode.SSRF_BLOCKED, f"Private network host blocked: {host}")

    blocked = [d.lower() for d in (blocked_domains or []) if d]
    for pattern in blocked:
        if _host_matches(host, pattern):
            raise BrowserError(BrowserErrorCode.DOMAIN_NOT_ALLOWED, f"Domain blocked: {host}")

    allowed = [d.lower() for d in (allowed_domains or []) if d]
    if allowed and not any(_host_matches(host, pattern) for pattern in allowed):
        raise BrowserError(
            BrowserErrorCode.DOMAIN_NOT_ALLOWED,
            f"Domain not in allowlist: {host}",
        )
    return url


def _is_localhost(host: str) -> bool:
    return host in {"localhost", "127.0.0.1", "::1", "[::1]"}


def _is_private_ip(host: str) -> bool:
    try:
        addr = ipaddress.ip_address(host)
        return addr.is_private or addr.is_loopback or addr.is_link_local
    except ValueError:
        if re.match(r"^(10\.|172\.(1[6-9]|2\d|3[01])\.|192\.168\.)", host):
            return True
        return host.endswith(".local") or host.endswith(".internal")
    return False


def _host_matches(host: str, pattern: str) -> bool:
    if pattern.startswith("*."):
        suffix = pattern[2:]
        return host == suffix or host.endswith(f".{suffix}")
    return host == pattern or host.endswith(f".{pattern}")
