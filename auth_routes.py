# auth_routes.py

from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from scripts.sql_alc.auth_models import Usuario
from scripts.py.auth_utils import AuthUtils
from database import get_db
import os
import json
from datetime import timedelta
from config import JWT_SECRET_KEY

auth_router = APIRouter(prefix="/auth", tags=["authentication"])
templates = Jinja2Templates(directory="templates")
auth_utils = AuthUtils(JWT_SECRET_KEY)

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
        
        # Buscar usuario por código
        usuario = db.query(Usuario).filter(Usuario.codigo == codigo).first()
        if not usuario:
            print(f"Usuario no encontrado: {codigo}")
            return templates.TemplateResponse(
                "auth/login.html",
                {"request": request, "error": "Código de usuario incorrecto"}
            )
        
        print(f"Usuario encontrado: {usuario.codigo}")
        
        # Verificar si la contraseña coincide con el código (caso inicial)
        # o con el hash almacenado (si ya se cambió la contraseña)
        is_valid = (password == usuario.codigo) or \
                  (usuario.password_hash and auth_utils.verify_password(password, usuario.password_hash))
        
        print(f"Validación de contraseña: {is_valid}")
        
        if not is_valid:
            return templates.TemplateResponse(
                "auth/login.html",
                {"request": request, "error": "Contraseña incorrecta"}
            )

        # Crear token y establecer cookies
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

        # Si la contraseña es el código, redirigir a cambio de contraseña
        if password == usuario.codigo:
            redirect_url = "/auth/change-password"
        else:
            # Determinar redirección según rol
            redirect_urls = {
                "Inventariador Proveedor": "/dashboard/proveedor",
                "Comisión Cliente": "/dashboard/comision",
                "Gerencial Proveedor": "/dashboard/gerencia"
            }
            redirect_url = redirect_urls.get(usuario.tipo_usuario, "/demo-inventario")

        # Crear respuesta y limpiar cookies anteriores
        response = RedirectResponse(url=redirect_url, status_code=302)
        
        # Limpiar cookies existentes
        response.delete_cookie(key="access_token")
        response.delete_cookie(key="session_data")
        
        # Establecer nuevas cookies
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
            max_age=3600 * 24 * 30,
            path="/",
            samesite="Lax"
        )
        
        print("Login completado exitosamente")
        return response

    except Exception as e:
        print(f"Error en login: {str(e)}")
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "error": "Error en el proceso de login"}
        )

@auth_router.get("/change-password", response_class=HTMLResponse)
async def change_password_page(request: Request):
    return templates.TemplateResponse("auth/change_password.html", {"request": request})

@auth_router.post("/change-password")
async def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        # Obtener datos de sesión
        session_data = request.cookies.get("session_data")
        if not session_data:
            return RedirectResponse(url="/auth/login", status_code=302)
        
        user_data = json.loads(session_data)
        usuario = db.query(Usuario).filter(Usuario.codigo == user_data["codigo"]).first()
        
        if not usuario:
            return templates.TemplateResponse(
                "auth/change_password.html",
                {"request": request, "error": "Usuario no encontrado"}
            )
        
        # Verificar contraseña actual
        valid_codigo = current_password == usuario.codigo
        valid_hash = False
        if usuario.password_hash:
            try:
                valid_hash = auth_utils.verify_password(current_password, usuario.password_hash)
            except Exception as e:
                print(f"Error verificando hash: {str(e)}")
        
        if not (valid_codigo or valid_hash):
            return templates.TemplateResponse(
                "auth/change_password.html",
                {"request": request, "error": "Contraseña actual incorrecta"}
            )
        
        # Verificar que las nuevas contraseñas coincidan
        if new_password != confirm_password:
            return templates.TemplateResponse(
                "auth/change_password.html",
                {"request": request, "error": "Las nuevas contraseñas no coinciden"}
            )
        
        # Actualizar contraseña
        usuario.password_hash = auth_utils.hash_password(new_password)
        db.commit()
        
        # Redireccionar según el rol
        redirect_urls = {
            "Inventariador Proveedor": "/dashboard/proveedor",
            "Comisión Cliente": "/dashboard/comision",
            "Gerencial Proveedor": "/dashboard/gerencia"
        }
        redirect_url = redirect_urls.get(usuario.tipo_usuario, "/demo-inventario")
        
        return RedirectResponse(url=redirect_url, status_code=302)
        
    except Exception as e:
        print(f"Error cambiando contraseña: {str(e)}")
        return templates.TemplateResponse(
            "auth/change_password.html",
            {"request": request, "error": f"Error al cambiar la contraseña: {str(e)}"}
        )

@auth_router.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/auth/login")
    response.delete_cookie("access_token")
    response.delete_cookie("session_data")
    return response

@auth_router.get("/reset-password/{usuario_id}")
async def reset_password(
    usuario_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Resetear la contraseña al código de usuario
        usuario.password_hash = auth_utils.hash_password(usuario.codigo)
        db.commit()

        return {"status": "success", "message": f"Contraseña reseteada para el usuario {usuario.codigo}"}

    except Exception as e:
        print(f"Error reseteando contraseña: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al resetear la contraseña")