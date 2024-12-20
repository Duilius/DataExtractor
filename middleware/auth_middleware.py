# middleware/auth_middleware.py
from fastapi import Request
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from scripts.py.auth_utils import AuthUtils
from config import JWT_SECRET_KEY
import json, jwt

class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.auth_utils = AuthUtils(JWT_SECRET_KEY)
        
        # Rutas completamente públicas
        self.public_paths = [
            "/auth/login",
            "/auth/logout",
            "/static",
            "/favicon.ico",
            "/docs",  # Si quieres que la documentación FastAPI sea pública
            "/openapi.json"
        ]
        
        # Rutas que requieren autenticación básica (todo usuario logueado)
        self.auth_paths = [
            "/dashboard",
            "/profile"
        ]
        
        # Rutas específicas por rol
        self.role_paths = {
            "Comisión Cliente": ["/dashboard/comision"],
            "Inventariador Proveedor": ["/dashboard/proveedor"],
            "Gerencial Proveedor": ["/dashboard/gerencia"]
        }

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        # 1. Permitir rutas públicas
        if any(request.url.path.startswith(path) for path in self.public_paths):
            return await call_next(request)
        
        # 2. Verificar autenticación
        access_token = request.cookies.get("access_token")
        session_data = request.cookies.get("session_data")
        
        if not access_token or not session_data:
            return RedirectResponse(url="/auth/login", status_code=302)
        
        try:
            # 3. Verificar token y obtener datos de usuario
            payload = jwt.decode(access_token, JWT_SECRET_KEY, algorithms=["HS256"])
            user_data = json.loads(session_data)
            request.state.user = user_data
            
            # 4. Verificar permisos por rol
            current_path = request.url.path
            user_role = user_data.get("tipo_usuario")
            
            # Si la ruta requiere un rol específico
            for role, paths in self.role_paths.items():
                if any(current_path.startswith(path) for path in paths):
                    if user_role != role:
                        return JSONResponse(
                            status_code=403,
                            content={"detail": "No tienes permisos para acceder a esta sección"}
                        )
            
            return await call_next(request)
            
        except Exception as e:
            print(f"Error en AuthMiddleware: {str(e)}")
            return RedirectResponse(url="/auth/login", status_code=302)