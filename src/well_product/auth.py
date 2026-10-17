"""Local desktop login gate (single fixed user, not network auth)."""

from __future__ import annotations

import hashlib
import hmac

_USERNAME = "admin"
# SHA-256 of UTF-8 password (admin!@#) — compare via digest, not plaintext in logic paths
_PASSWORD_HASH = hashlib.sha256(b"admin!@#").hexdigest()


def validate_credentials(username: str, password: str) -> bool:
    if not username or not password:
        return False
    user_ok = hmac.compare_digest(username.strip().encode("utf-8"), _USERNAME.encode("utf-8"))
    pwd_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    pwd_ok = hmac.compare_digest(pwd_hash.encode("utf-8"), _PASSWORD_HASH.encode("utf-8"))
    return user_ok and pwd_ok
