"""NovelAI credential validation and access-key derivation."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import blake2b
import secrets
import string


@dataclass(frozen=True, slots=True)
class NovelAICredentials:
    token: str | None = None
    username: str | None = None
    password: str | None = None

    def __post_init__(self) -> None:
        has_pair = bool(self.username and self.password)
        has_partial_pair = bool(self.username) != bool(self.password)
        if has_partial_pair or not (self.token or has_pair):
            raise ValueError("provide a token or a complete username/password pair")


def derive_access_key(credentials: NovelAICredentials) -> str:
    """Derive the 64-character NovelAI login key from username/password."""
    if not credentials.username or not credentials.password:
        raise ValueError("username/password credentials are required")
    try:
        from argon2.low_level import Type, hash_secret_raw
    except ImportError as exc:
        raise RuntimeError(
            "install the novelai extra for username/password login"
        ) from exc

    # blake2b derives a 16-byte deterministic salt for the argon2id call below;
    # it is NOT the password hash. Construction is mandated by NovelAI's
    # novelai_data_access_key protocol; altering breaks upstream compatibility.
    # CodeQL py/weak-sensitive-data-hashing flagged this as false positive
    # (dismissed: alert #1).
    salt_source = (
        f"{credentials.password[:6]}{credentials.username}novelai_data_access_key"
    )
    salt = blake2b(salt_source.encode(), digest_size=16).digest()
    derived = hash_secret_raw(
        secret=credentials.password.encode(),
        salt=salt,
        time_cost=2,
        memory_cost=1_953,
        parallelism=1,
        hash_len=64,
        type=Type.ID,
    )
    return base64.urlsafe_b64encode(derived).decode()[:64]


def request_tracking_headers() -> dict[str, str]:
    """Build fresh tracking headers expected by NovelAI's browser-facing APIs."""
    alphabet = string.ascii_letters + string.digits
    correlation_id = "".join(secrets.choice(alphabet) for _ in range(6))
    initiated_at = (
        datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    )
    return {
        "x-correlation-id": correlation_id,
        "x-initiated-at": initiated_at,
    }
