from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from fastapi import HTTPException
from typing import Optional

# Modificar la inicialización de CryptContext
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__default_rounds=12,  # Establecer rondas explícitamente
    bcrypt__ident="2b"         # Usar identificador específico
)

class AuthUtils:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key

    def hash_password(self, password: str) -> str:
        try:
            return pwd_context.hash(password)
        except Exception as e:
            print(f"Error al hashear password: {str(e)}")
            # Podemos intentar un fallback o re-lanzar el error
            raise
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = {k: str(v) for k, v in data.items()}
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=30)
        to_encode.update({"exp": expire.timestamp()})
        encoded_jwt = jwt.encode(to_encode, str(self.secret_key), algorithm="HS256")
        return encoded_jwt

    def verify_access_token(self, token: str):
        try:
            payload = jwt.decode(token, str(self.secret_key), algorithms=["HS256"])
            return payload
        except ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expirado")
        except InvalidTokenError:
            raise HTTPException(status_code=401, detail="Token inválido")
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Error verificando token: {str(e)}")

    def get_current_datetime(self):
        return datetime.now()
    
    def validate_password(self, password: str) -> tuple[bool, str]:
        """Valida requisitos de contraseña"""
        if len(password) < 8:
            return False, "La contraseña debe tener al menos 8 caracteres"
        return True, ""