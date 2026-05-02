import base64
from cryptography.fernet import Fernet


class EncryptionService:
    def __init__(self, key: str):
        # Accept any string; pad/normalize to a valid 32-byte Fernet key if needed
        key_bytes = key.encode() if isinstance(key, str) else key
        try:
            self._fernet = Fernet(key_bytes)
        except Exception:
            padded = (key.encode() + b"\x00" * 32)[:32]
            self._fernet = Fernet(base64.urlsafe_b64encode(padded))

    def encrypt(self, value: str) -> str:
        return self._fernet.encrypt(value.encode()).decode()

    def decrypt(self, token: str) -> str:
        return self._fernet.decrypt(token.encode()).decode()
