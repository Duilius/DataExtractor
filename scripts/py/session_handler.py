from datetime import datetime, timedelta, UTC
from fastapi import Request, Response
import json

class SessionHandler:
    def __init__(self):
        self.session_duration = 12 * 3600  # 12 horas en segundos
        self.inactivity_timeout = 30 * 60  # 30 minutos en segundos

    def validate_session(self, request: Request) -> bool:
        """Valida si la sesión está activa y no ha expirado"""
        try:
            access_token = request.cookies.get("access_token")
            session_data = request.cookies.get("session_data")
            
            if not access_token or not session_data:
                return False
                
            session_data = json.loads(session_data)
            last_activity = session_data.get("last_activity", 0)
            
            # Verificar si ha pasado más tiempo del permitido
            if (datetime.now(UTC).timestamp() - last_activity) > self.inactivity_timeout:
                return False
            
            return True
        except:
            return False

    def renew_session_if_active(self, request: Request, response: Response) -> bool:
        """Renueva la sesión si hay actividad del usuario"""
        try:
            access_token = request.cookies.get("access_token")
            session_data = request.cookies.get("session_data")
            
            if access_token and session_data:
                # Actualizar timestamp de última actividad
                session_data_dict = json.loads(session_data)
                session_data_dict["last_activity"] = datetime.now(UTC).timestamp()
                
                # Renovar la expiración
                response.set_cookie(
                    key="access_token",
                    value=access_token,
                    httponly=True,
                    max_age=self.session_duration,
                    secure=True,
                    samesite="lax"
                )
                
                response.set_cookie(
                    key="session_data",
                    value=json.dumps(session_data_dict),
                    httponly=False,
                    max_age=self.session_duration,
                    samesite="Lax"
                )
                
                return True
        except:
            pass
        return False

    def clear_session(self, response: Response) -> Response:
        """Limpia todas las cookies de sesión"""
        response.delete_cookie(key="access_token")
        response.delete_cookie(key="session_data")
        return response

    def get_session_info(self, request: Request) -> dict:
        """Obtiene información de la sesión actual"""
        try:
            session_data = json.loads(request.cookies.get("session_data", "{}"))
            if session_data:
                expiry = session_data.get("last_activity", 0) + self.session_duration
                remaining = expiry - datetime.now(UTC).timestamp()
                return {
                    "active": True,
                    "expires_in": int(remaining),
                    "last_activity": session_data.get("last_activity", 0),
                    "user_data": {
                        "id": session_data.get("id"),
                        "codigo": session_data.get("codigo"),
                        "tipo_usuario": session_data.get("tipo_usuario")
                    }
                }
        except:
            pass
        return {"active": False}

# Crear una instancia global
session_handler = SessionHandler()