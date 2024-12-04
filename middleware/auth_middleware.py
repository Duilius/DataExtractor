from fastapi import Request
from fastapi.responses import RedirectResponse
from scripts.py.auth_utils import AuthUtils
from scripts.py.session_handler import session_handler  # Añadir esta importación
import os
from typing import List
from starlette.middleware.base import BaseHTTPMiddleware

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
        if any(request.url.path.startswith(path) for path in self.public_paths):
            response = await call_next(request)
            return response

        access_token = request.cookies.get("access_token")
        if not access_token:
            return RedirectResponse(url="/auth/login", status_code=302)

        try:
            payload = self.auth_utils.verify_access_token(access_token)
            request.state.user = payload
            response = await call_next(request)
            # Renovar sesión si hay actividad
            session_handler.renew_session_if_active(request, response)
            return response
        except:
            return RedirectResponse(url="/auth/login", status_code=302)