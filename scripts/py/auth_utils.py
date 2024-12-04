from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer
import time
from typing import Optional, Dict

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
security = HTTPBearer()

class AuthUtils:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self._rate_limit_data: Dict[str, list] = {}
    
    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = {k: str(v) for k, v in data.items()}
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=12)
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
    
    def check_rate_limit(self, ip: str, max_attempts: int = 5, window_seconds: int = 300):
        now = time.time()
        if ip in self._rate_limit_data:
            self._rate_limit_data[ip] = [t for t in self._rate_limit_data[ip] 
                                       if now - t < window_seconds]
        
        attempts = len(self._rate_limit_data.get(ip, []))
        if attempts >= max_attempts:
            raise HTTPException(
                status_code=429,
                detail=f"Demasiados intentos. Por favor espere {window_seconds//60} minutos."
            )
        
        if ip not in self._rate_limit_data:
            self._rate_limit_data[ip] = []
        self._rate_limit_data[ip].append(now)
    
    def check_access_hours(self, user_type: str) -> bool:
        current_time = datetime.now().time()
        current_weekday = datetime.now().weekday()
        
        if user_type in ['Inventariador Proveedor', 'Inventariador Cliente']:
            if current_weekday < 5:  # Lunes a Viernes
                if current_time.hour >= 8 and current_time.hour < 17:
                    return True
            return current_time.hour >= 17
        
        return True

    def get_current_datetime(self):
        return datetime.now()