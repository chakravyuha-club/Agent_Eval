"""
Password hashing (stdlib only, no new dependency).

Format:  pbkdf2_sha256$<iterations>$<salt_b64>$<hash_b64>
Legacy:  pbkdf2_sha256$<salt_hex>$<hash_hex>      (100k iterations; accepted, flagged for rehash on login)
"""
import base64
import hashlib
import hmac
import os
from typing import Tuple

RECOMMENDED_ITERATIONS = 600_000   # OWASP guidance for PBKDF2-HMAC-SHA256
# Lower ONLY in dev/tests to speed up seeding (e.g. PASSWORD_HASH_ITERATIONS=20000). Pre-flight flags this in prod.
ITERATIONS = int(os.environ.get("PASSWORD_HASH_ITERATIONS", RECOMMENDED_ITERATIONS))
LEGACY_ITERATIONS = 100_000
MIN_PASSWORD_LENGTH = 12


def _b64(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")


def validate_password_strength(password: str) -> None:
    """Raises ValueError with an actionable message."""
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    if len(password) > 256:
        raise ValueError("Password is too long.")
    if password.lower() == password or password.upper() == password or not any(c.isdigit() for c in password):
        raise ValueError("Password must mix upper/lower case letters and include a digit.")


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${_b64(salt)}${_b64(dk)}"


def verify_and_check_rehash(password: str, stored: str) -> Tuple[bool, bool]:
    """Returns (is_valid, needs_rehash). Constant-time comparison."""
    try:
        parts = (stored or "").split("$")
        if len(parts) == 4 and parts[0] == "pbkdf2_sha256":
            iters, salt, expected = int(parts[1]), base64.b64decode(parts[2]), base64.b64decode(parts[3])
            dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iters)
            return hmac.compare_digest(dk, expected), iters < ITERATIONS
        if len(parts) == 3 and parts[0] == "pbkdf2_sha256":  # legacy: salt is a hex STRING used as bytes
            dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), parts[1].encode("utf-8"), LEGACY_ITERATIONS).hex()
            return hmac.compare_digest(dk, parts[2]), True
    except Exception:
        pass
    return False, False


def verify_password(password: str, stored: str) -> bool:
    return verify_and_check_rehash(password, stored)[0]


# Used to burn the same CPU time when the account does not exist (no user-enumeration by timing).
DUMMY_HASH = hash_password("dummy-password-for-timing-Equalisation-1")
