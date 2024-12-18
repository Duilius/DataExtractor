from fastapi import Request
from fastapi.responses import RedirectResponse, JSONResponse
from scripts.py.auth_utils import AuthUtils
from scripts.py.session_handler import session_handler
import os
from typing import List
from starlette.middleware.base import BaseHTTPMiddleware
from config import JWT_SECRET_KEY

# Crear instancia de AuthUtils
auth_utils = AuthUtils(JWT_SECRET_KEY)


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, public_paths: List[str] = None):
        super().__init__(app)
        self.auth_utils = AuthUtils(os.getenv("JWT_SECRET_KEY"))
        self.public_paths = public_paths or [
            "/auth/login",
            "/auth/logout",
            "/auth/renew-session",
            "/static",
            "/favicon.ico",
            "/"
        ]
    
    async def dispatch(self, request: Request, call_next):
        """
        Middleware para autenticar usuarios mediante JWT y gestionar sesiones activas.
        """
        # Permitir acceso a rutas públicas sin autenticación
        if any(request.url.path.startswith(path) for path in self.public_paths):
            print(f"Middleware Auth: Request Path -> {request.url.path}")
            response = await call_next(request)
            print(f"Middleware Auth: Response Status -> {response.status_code}")
            return response
            

        # Obtener el token desde las cookies
        access_token = request.cookies.get("access_token")
        if not access_token:
            # Si no hay token, redirigir al login
            return RedirectResponse(url="/auth/login", status_code=302)

        try:
            # Verificar la validez del token
            payload = self.auth_utils.verify_access_token(access_token)
            request.state.user = payload  # Añadir usuario a request.state
            response = await call_next(request)
            # Renovar sesión si hay actividad
            session_handler.renew_session_if_active(request, response)
            return response
        except Exception as e:
            # Manejar errores en la verificación del token
            print(f"AuthMiddleware Error: {e}")  # Registrar error
            return RedirectResponse(url="/auth/login", status_code=302)


# ************* VALIDACIÓN DE SESIONES ****************
async def validate_session(request: Request, call_next):
    """
    Middleware para validar sesiones activas.
    """
    token = request.cookies.get("access_token")
    if token:
        try:
            # Verificar el token y obtener datos
            payload = auth_utils.verify_access_token(token)
            user_id = str(payload.get("sub"))
            
            # Verificar si el token sigue siendo válido
            if not auth_utils.is_token_active(user_id, token):
                # Sesión inválida, eliminar cookies
                response = JSONResponse(
                    status_code=401,
                    content={"detail": "Sesión invalidada por inicio de sesión en otro dispositivo"}
                )
                response.delete_cookie("access_token")
                response.delete_cookie("session_data")
                return response
                
        except Exception as e:
            print(f"Validate Session Error: {e}")  # Registrar error
    
    # Continuar al siguiente middleware o endpoint
    return await call_next(request)
