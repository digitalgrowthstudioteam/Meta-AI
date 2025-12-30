"""
Magic Link Token Utilities
- Token generation
- Token hashing
- Token verification helpers

Rules:
- NEVER store raw tokens
- Tokens are single-use (enforced via DB elsewhere)
- Expiry: 10 minutes (LOCKED)
- Pure logic only (NO DB writes here)
"""

import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Tuple

# =========================================================
# CONSTANTS (LOCKED)
# =========================================================
MAGIC_LINK_EXPIRE_MINUTES = 10


# =========================================================
# TOKEN GENERATION
# =========================================================
def generate_magic_token() -> str:
    """
    Generate a cryptographically secure random token.
    This raw token is sent to the user via email.
    """
    return secrets.token_urlsafe(32)


def hash_magic_token(raw_token: str) -> str:
    """
    Hash the raw token before storing in DB.
    SHA-256 is sufficient because:
    - Token is random
    - Short-lived
    - Single-use
    """
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_magic_token_pair() -> Tuple[str, str]:
    """
    Create a raw token + hashed token pair.

    Returns:
        (raw_token, token_hash)
    """
    raw_token = generate_magic_token()
    token_hash = hash_magic_token(raw_token)
    return raw_token, token_hash


# =========================================================
# EXPIRY HELPERS
# =========================================================
def magic_token_expiry() -> datetime:
    """
    Returns expiry datetime for magic token.
    Uses UTC internally (conversion to IST happens elsewhere).
    """
    return datetime.now(timezone.utc) + timedelta(minutes=MAGIC_LINK_EXPIRE_MINUTES)


def is_token_expired(expires_at: datetime) -> bool:
    """
    Check whether a token has expired.
    """
    return datetime.now(timezone.utc) >= expires_at
