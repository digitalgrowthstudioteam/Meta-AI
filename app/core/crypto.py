import os
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


class CryptoService:
    _fernet: Optional[Fernet] = None

    @classmethod
    def _get_fernet(cls) -> Fernet:
        """
        Lazy init Fernet instance.
        Raises RuntimeError if ENCRYPTION_KEY not set in .env
        """
        if cls._fernet is None:
            key = os.getenv("ENCRYPTION_KEY") or None
            if not key:
                raise RuntimeError(
                    "ENCRYPTION_KEY is not set. Please add it to your .env file."
                )
            cls._fernet = Fernet(key.encode() if isinstance(key, str) else key)
        return cls._fernet

    @classmethod
    def encrypt_secret(cls, value: str) -> str:
        """
        Encrypts a string using Fernet and returns base64 encoded token.
        """
        if value is None:
            return None
        f = cls._get_fernet()
        return f.encrypt(value.encode()).decode()

    @classmethod
    def decrypt_secret(cls, token: str) -> str:
        """
        Decrypts base64 encoded Fernet token and returns string.
        Raises InvalidToken if corrupted or wrong key.
        """
        if token is None:
            return None
        f = cls._get_fernet()
        try:
            return f.decrypt(token.encode()).decode()
        except InvalidToken as e:
            raise InvalidToken("Failed to decrypt secret. Possibly wrong key or corrupt.") from e
