from passlib.context import CryptContext
from passlib.handlers.bcrypt import bcrypt
from datetime import datetime, timedelta
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer
import time
from typing import Optional, Dict


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Agregar esta línea
)

security = HTTPBearer()

class AuthUtils:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self._rate_limit_data: Dict[str, list] = {}
        self._active_sessions: Dict[str, dict] = {}  # usuario_id: {token, last_check}

    
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
        
        # Inicializar si no existe
        if ip not in self._rate_limit_data:
            self._rate_limit_data[ip] = []
        
        # Limpiar intentos antiguos
        self._rate_limit_data[ip] = [t for t in self._rate_limit_data[ip] 
                                    if now - t < window_seconds]
        
        # Verificar intentos
        attempts = len(self._rate_limit_data[ip])
        if attempts >= max_attempts:
            raise HTTPException(
                status_code=429,
                detail=f"Demasiados intentos. Por favor espere {window_seconds//60} minutos."
            )
        
        # Registrar nuevo intento
        self._rate_limit_data[ip].append(now)


    """def check_access_hours(self, user_type: str) -> bool:
        current_time = datetime.now().time()
        current_weekday = datetime.now().weekday()
        
        if user_type in ['Inventariador Proveedor', 'Inventariador Cliente']:
            if current_weekday < 5:  # Lunes a Viernes
                return current_time.hour >= 8 and current_time.hour < 17
            return False  # No acceso en fin de semana
        
        return True"""

    def get_current_datetime(self):
        return datetime.now()

    def register_session(self, user_id: str, token: str) -> None:
        """Registra una nueva sesión"""
        self._active_sessions[user_id] = {
            'token': token,
            'last_check': time.time()
        }

    def check_active_session(self, user_id: str) -> bool:
        """Verifica si existe una sesión activa válida"""
        if user_id in self._active_sessions:
            session = self._active_sessions[user_id]
            try:
                self.verify_access_token(session['token'])
                # Actualizar último chequeo
                self._active_sessions[user_id]['last_check'] = time.time()
                return True
            except:
                del self._active_sessions[user_id]
        return False
    
        
    def is_token_active(self, user_id: str, token: str) -> bool:
        """Verifica si el token es el último emitido para el usuario"""
        session = self._active_sessions.get(user_id)
        return session and session['token'] == token

    def generate_reset_token(self, user_data: dict) -> str:
        """Genera token para reset de password"""
        return self.create_access_token(
            data=user_data,
            expires_delta=timedelta(hours=24)
        )

    def verify_reset_token(self, token: str) -> dict:
        """Verifica token de reset"""
        return self.verify_access_token(token)

    def validate_password(self, password: str) -> tuple[bool, str]:
        """Valida requisitos de contraseña"""
        if len(password) < 8:
            return False, "Mínimo 8 caracteres"
        if not any(c.isupper() for c in password):
            return False, "Requiere mayúscula"
        if not any(c.islower() for c in password):
            return False, "Requiere minúscula"
        if not any(c.isdigit() for c in password):
            return False, "Requiere número"
        return True, ""
    
    #********** LIMPIAR SESIONES EXPIRADAS *************
    def cleanup_expired_sessions(self):
        """Limpia sesiones expiradas o inactivas por más de 15 minutos"""
        now = time.time()
        to_remove = []
        for user_id, session in self._active_sessions.items():
            if now - session['last_check'] > 900:  # 15 minutos
                to_remove.append(user_id)
        
        for user_id in to_remove:
            del self._active_sessions[user_id]


    #****** MÉTODO DE FUERZA BRUTA PARA LIMPIAR SESSION ***********
    def force_cleanup_session(self, user_id: str) -> None:
        """Limpia forzosamente la sesión de un usuario"""
        if user_id in self._active_sessions:
            del self._active_sessions[user_id]
            print(f"Sesión forzosamente limpiada para usuario: {user_id}")