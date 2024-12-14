from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from scripts.sql_alc.auth_models import Usuario, TipoUsuario
from scripts.py.auth_utils import AuthUtils
from database import get_db
import os
import json
from config import JWT_SECRET_KEY
from datetime import timedelta

auth_router = APIRouter(prefix="/auth", tags=["authentication"])
templates = Jinja2Templates(directory="templates")
auth_utils = AuthUtils(JWT_SECRET_KEY)  # Usar la constante

#JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "una_clave_secreta_muy_larga_y_segura_para_jwt_tokens_12345")

#auth_router = APIRouter(prefix="/auth", tags=["authentication"])
#templates = Jinja2Templates(directory="templates")
#auth_utils = AuthUtils(JWT_SECRET_KEY)

@auth_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})


@auth_router.post("/login")
async def login(
    request: Request,
    codigo: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        print(f"Intento de login para código: {codigo}")
        
        usuario = db.query(Usuario).filter(Usuario.codigo == codigo).first()
        if not usuario:
            return templates.TemplateResponse(
                "auth/login.html",
                {"request": request, "error": "Usuario o contraseña incorrectos"}
            )
        
        if not auth_utils.verify_password(password, usuario.password_hash):
            return templates.TemplateResponse(
                "auth/login.html",
                {"request": request, "error": "Usuario o contraseña incorrectos"}
            )
        
        access_token = auth_utils.create_access_token(
            data={"sub": usuario.codigo, "type": usuario.tipo_usuario}
        )
        
        session_data = {
            "id": usuario.id,
            "codigo": usuario.codigo,
            "tipo_usuario": usuario.tipo_usuario,
            "institucion_id": usuario.institucion_id,
            "sede_actual_id": usuario.sede_actual_id
        }

        # Determinar redirección
        if usuario.tipo_usuario == "Inventariador Proveedor":
            redirect_url = "/dashboard/proveedor"
        elif usuario.tipo_usuario == "Comisión Cliente":
            redirect_url = "/dashboard/comision"
        elif usuario.tipo_usuario == "Gerencial Proveedor":
            redirect_url = "/dashboard/gerencial"
        else:
            redirect_url = "/demo-inventario"

        # Crear respuesta
        if usuario.requiere_cambio_password:
            response = RedirectResponse(url="/auth/change-password", status_code=302)
        else:
            response = RedirectResponse(url=redirect_url, status_code=302)

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=3600 * 24 * 30,
            secure=True,
            samesite="lax"
        )
        
        response.set_cookie(
            key="session_data",
            value=json.dumps(session_data),
            httponly=False,
            max_age=3600 * 24 *30,
            path="/",
            samesite="Lax"
        )
        
        usuario.ultimo_acceso = auth_utils.get_current_datetime()
        db.commit()
        
        print("Login completado exitosamente")
        return response

    except Exception as e:
        print(f"Error en login: {str(e)}")
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "error": "Error en el proceso de login"}
        )