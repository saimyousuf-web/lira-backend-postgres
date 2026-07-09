from uuid import UUID

from cryptography.fernet import Fernet

from core.config import settings

FERNET_KEY=settings.FERNET_KEY

if not FERNET_KEY:
    raise RuntimeError("FERNET_KEY not configured")

cipher = Fernet(FERNET_KEY.encode())


def encrypt_id(value) -> str:
    return cipher.encrypt(str(value).encode()).decode()


def decrypt_id(token: str) -> UUID:
    decrypted = cipher.decrypt(token.encode()).decode()
    return UUID(decrypted)
# def decrypt_id(token: str):
#     return cipher.decrypt(token.encode()).decode()