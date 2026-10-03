"""
SSRF Protection and URL Sandboxing
Validates target hostnames and IPs against private, loopback, and metadata ranges.
"""
import ipaddress
import socket
from urllib.parse import urlparse
from typing import Tuple, Optional

# Prohibited CIDR networks
BLOCKED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),       # Link-local and AWS/GCP/Azure Metadata
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("192.88.99.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("224.0.0.0/4"),          # Multicast
    ipaddress.ip_network("240.0.0.0/4"),
    ipaddress.ip_network("255.255.255.255/32"),
    ipaddress.ip_network("::1/128"),              # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),             # IPv6 Unique local
    ipaddress.ip_network("fe80::/10"),            # IPv6 Link-local
]

def is_ip_prohibited(ip_str: str) -> bool:
    """Checks whether an IP address belongs to private, loopback, or metadata CIDR ranges."""
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_multicast or ip_obj.is_reserved:
            return True
        for net in BLOCKED_NETWORKS:
            if ip_obj in net:
                return True
        return False
    except ValueError:
        return True

def validate_target_url(url: str, allow_localhost_for_testing: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Validates a submitted application URL against SSRF attacks.
    Returns (is_valid: bool, error_message: Optional[str]).
    """
    if not url or not isinstance(url, str):
        return False, "URL cannot be empty."
    
    parsed = urlparse(url)
    if parsed.scheme not in ["http", "https"]:
        return False, f"Invalid URL scheme '{parsed.scheme}'. Only 'http' and 'https' are permitted."
    
    hostname = parsed.hostname
    if not hostname:
        return False, "Invalid URL: missing hostname."
    
    if hostname.lower() in ["localhost", "127.0.0.1", "::1", "metadata.google.internal"] and not allow_localhost_for_testing:
        return False, "Forbidden target host: Loopback/localhost destinations are prohibited."
    
    # If in dev/test mode and localhost is explicitly allowed for mock agents
    if allow_localhost_for_testing and hostname.lower() in ["localhost", "127.0.0.1"]:
        return True, None

    try:
        # Resolve all DNS A/AAAA records
        addr_info = socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
        for res in addr_info:
            ip = res[4][0]
            if is_ip_prohibited(ip):
                return False, f"Security Violation: Target host resolves to restricted IP address ({ip})."
    except socket.gaierror:
        return False, f"DNS Resolution failed for host '{hostname}'."
    except Exception as e:
        return False, f"URL validation error: {str(e)}"
    
    return True, None
