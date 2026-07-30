"""
Phase 4 Token Cryptography Engine

Provides symmetric Fernet encryption/decryption for OAuth 2.0 access and refresh tokens.
Uses dedicated settings.FERNET_KEY (independent of SECRET_KEY).
"""
import base64
import hashlib
from cryptography.fernet import Fernet
from app.core.config import settings


def _get_fernet() -> Fernet:
    key_str = settings.FERNET_KEY
    try:
        # Check if valid base64 key
        raw_key = key_str.encode('utf-8')
        base64.urlsafe_b64decode(raw_key)
        if len(base64.urlsafe_b64decode(raw_key)) == 32:
            return Fernet(raw_key)
    except Exception:
        pass

    # Fallback to sha256 derived key if invalid Fernet string supplied
    derived = base64.urlsafe_b64encode(hashlib.sha256(key_str.encode('utf-8')).digest())
    return Fernet(derived)


def encrypt_token(plain_text: str) -> str:
    """Encrypt a plain text token string into an encrypted Fernet string."""
    if not plain_text:
        return ""
    f = _get_fernet()
    return f.encrypt(plain_text.encode('utf-8')).decode('utf-8')


def decrypt_token(cipher_text: str) -> str:
    """Decrypt an encrypted Fernet string back into plain text token."""
    if not cipher_text:
        return ""
    f = _get_fernet()
    return f.decrypt(cipher_text.encode('utf-8')).decode('utf-8')
