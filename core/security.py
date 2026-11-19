import jwt
from datetime import datetime, timezone, timedelta
from typing import Optional
from pwdlib import PasswordHash
from core.config import settings

# 1. Argon2 Modern Password Hashing
password_hasher = PasswordHash.recommended()

def hash_password(password: str) -> str:
    """Hashes a plain text password with Argon2."""
    return password_hasher.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against an Argon2 hash."""
    return password_hasher.verify(plain_password, hashed_password)

# 2. Cryptographic JWT Token Engine
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a cryptographically signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_access_token(token: str) -> Optional[dict]:
    """
    Decodes and verifies a JWT token.
    Returns payload if signature & expiration are valid, else None.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
