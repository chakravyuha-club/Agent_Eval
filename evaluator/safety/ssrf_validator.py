"""
SSRF Protection and URL Sandboxing (hardened).

Changes vs. original:
  * Uses ipaddress `is_global` (deny-by-default) and unwraps IPv4-mapped IPv6.
  * `validate_and_resolve()` returns the validated IPs so the HTTP client can PIN the
    connection to them (defeats DNS-rebinding TOCTOU between check and connect).
  * HTTPS-only + port allow-list + no userinfo + URL length cap (strict mode).
  * Localhost bypass is ignored when ENVIRONMENT=production (fail-closed).
  * `validate_target_url()` keeps its legacy (bool, msg) contract for existing callers/tests.
"""
import ipaddress
import os
import socket
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple
from urllib.parse import urlparse

MAX_URL_LENGTH = 2048
DEFAULT_ALLOWED_PORTS: Tuple[int, ...] = (443, 8443)

# Extra explicit ranges (documentation / benchmarking / 6to4 relay / NAT64 etc.).
# `is_global` already rejects most of these; kept explicit for audit readability.
BLOCKED_NETWORKS = [ipaddress.ip_network(n) for n in (
    "0.0.0.0/8", "10.0.0.0/8", "100.64.0.0/10", "127.0.0.0/8", "169.254.0.0/16",
    "172.16.0.0/12", "192.0.0.0/24", "192.0.2.0/24", "192.88.99.0/24", "192.168.0.0/16",
    "198.18.0.0/15", "198.51.100.0/24", "203.0.113.0/24", "224.0.0.0/4", "240.0.0.0/4",
    "255.255.255.255/32", "::/128", "::1/128", "fc00::/7", "fe80::/10", "ff00::/8",
    "64:ff9b::/96", "2001:db8::/32", "2002::/16",
)]

LOOPBACK_NAMES = {"localhost", "localhost.localdomain", "ip6-localhost", "metadata.google.internal"}


def _production() -> bool:
    return os.environ.get("ENVIRONMENT", "development").lower() == "production"


def is_ip_prohibited(ip_str: str) -> bool:
    """True if the address is not a plain public unicast address (deny-by-default)."""
    try:
        ip = ipaddress.ip_address(ip_str.split("%")[0])
    except ValueError:
        return True
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped  # ::ffff:127.0.0.1 must be judged as 127.0.0.1
    if not ip.is_global:
        return True
    return any(ip in net for net in BLOCKED_NETWORKS)


@dataclass
class ResolvedTarget:
    scheme: str
    hostname: str
    port: int
    path: str
    ips: List[str] = field(default_factory=list)  # validated, connect to these only


def validate_and_resolve(
    url: str,
    *,
    require_https: bool = True,
    allowed_ports: Optional[Sequence[int]] = DEFAULT_ALLOWED_PORTS,
    allow_localhost_for_testing: bool = False,
) -> Tuple[bool, Optional[str], Optional[ResolvedTarget]]:
    """Strict validation. Returns (ok, error, ResolvedTarget)."""
    if allow_localhost_for_testing and _production():
        allow_localhost_for_testing = False  # never honoured in production
    if not url or not isinstance(url, str):
        return False, "URL cannot be empty.", None
    if len(url) > MAX_URL_LENGTH:
        return False, "URL is too long.", None
    try:
        parsed = urlparse(url.strip())
        port_in_url = parsed.port  # raises ValueError on bad port
    except ValueError:
        return False, "Malformed URL.", None

    schemes = ("https",) if require_https else ("http", "https")
    if parsed.scheme not in schemes:
        which = "'https'" if require_https else "'http' and 'https'"
        return False, f"Invalid URL scheme '{parsed.scheme}'. Only {which} are permitted.", None
    if parsed.username or parsed.password:
        return False, "Credentials in URL are not permitted.", None
    hostname = parsed.hostname
    if not hostname:
        return False, "Invalid URL: missing hostname.", None
    hostname = hostname.rstrip(".").lower()
    port = port_in_url or (443 if parsed.scheme == "https" else 80)
    path = parsed.path or ""

    if hostname in LOOPBACK_NAMES or hostname in ("127.0.0.1", "::1"):
        if allow_localhost_for_testing and hostname in ("localhost", "127.0.0.1", "::1"):
            return True, None, ResolvedTarget(parsed.scheme, hostname, port, path, ["127.0.0.1"])
        return False, "Forbidden target host: Loopback/localhost destinations are prohibited.", None

    if allowed_ports is not None and port not in allowed_ports:
        return False, f"Port {port} is not permitted.", None

    try:
        infos = socket.getaddrinfo(hostname, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        return False, f"DNS Resolution failed for host '{hostname}'.", None
    except Exception:
        return False, "URL validation error.", None

    ips: List[str] = []
    for info in infos:
        ip = info[4][0]
        if is_ip_prohibited(ip):
            return False, "Security Violation: Target host resolves to a restricted IP address.", None
        if ip not in ips:
            ips.append(ip)
    if not ips:
        return False, f"DNS Resolution failed for host '{hostname}'.", None
    return True, None, ResolvedTarget(parsed.scheme, hostname, port, path, ips)


def validate_target_url(url: str, allow_localhost_for_testing: bool = False) -> Tuple[bool, Optional[str]]:
    """Legacy contract kept for existing callers: (is_valid, error). Accepts http+https, any port."""
    ok, err, _ = validate_and_resolve(
        url, require_https=False, allowed_ports=None,
        allow_localhost_for_testing=allow_localhost_for_testing,
    )
    return ok, err
