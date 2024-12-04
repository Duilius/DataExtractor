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
        
        # Verificar rate limit
        client_ip = request.client.host
        auth_utils.check_rate_limit(client_ip)
        
        # Buscar usuario
        usuario = db.query(Usuario).filter(Usuario.codigo == codigo).first()
        if not usuario:
            print("Usuario no encontrado")
            return templates.TemplateResponse(
                "auth/login.html",
                {
                    "request": request,
                    "error": "Usuario o contraseña incorrectos"
                }
            )
        
        # Verificar contraseña
        if not auth_utils.verify_password(password, usuario.password_hash):
            usuario.intentos_fallidos += 1
            db.commit()
            print(f"Intento fallido #{usuario.intentos_fallidos}")
            
            mensaje_error = "Usuario o contraseña incorrectos"
            if usuario.intentos_fallidos >= 5:
                usuario.esta_activo = False
                db.commit()
                mensaje_error = "Cuenta bloqueada por múltiples intentos fallidos"
            
            return templates.TemplateResponse(
                "auth/login.html",
                {
                    "request": request,
                    "error": mensaje_error
                }
            )

        # Verificar si la cuenta está activa
        if not usuario.esta_activo:
            return templates.TemplateResponse(
                "auth/login.html",
                {
                    "request": request,
                    "error": "Cuenta bloqueada. Contacte al administrador"
                }
            )

        # Verificar horario de acceso
        if not auth_utils.check_access_hours(usuario.tipo_usuario):
            return templates.TemplateResponse(
                "auth/login.html",
                {
                    "request": request,
                    "error": "Acceso no permitido en este horario"
                }
            )
        
        print("Credenciales válidas, creando sesión")
        
        # Crear datos de sesión para el cliente
        session_data = {
            "id": usuario.id,
            "codigo": usuario.codigo,
            "tipo_usuario": usuario.tipo_usuario,
            "institucion_id": usuario.institucion_id,
             "sede_actual_id": usuario.sede_actual_id  # Aquí está el cambio
        }

        # Determinar la redirección según el tipo de usuario
        if usuario.tipo_usuario == "Inventariador Proveedor":
            redirect_url = "/dashboard/proveedor"
        elif usuario.tipo_usuario == "Comisión Cliente":
            redirect_url = "/dashboard/comision"
        elif usuario.tipo_usuario == "Gerencial Proveedor":
            redirect_url = "/dashboard/gerencial"
        else:
            redirect_url = "/demo-inventario"  # ruta por defecto

        # Crear token y establecer cookies
        access_token = auth_utils.create_access_token(
            data={"sub": usuario.codigo, "type": usuario.tipo_usuario}
        )
        
        # Si requiere cambio de contraseña, redirigir a la página de cambio
        if usuario.requiere_cambio_password:
            response = RedirectResponse(url="/auth/change-password", status_code=302)
        else:
            response = RedirectResponse(url=redirect_url, status_code=302)
        
        # Cookie para autenticación
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=3600 * 12,
            secure=True,
            samesite="lax"
        )
        
        # Cookie para datos de sesión del cliente
        response.set_cookie(
            key="session_data",
            value=json.dumps(session_data),
            httponly=False,
            max_age=3600 * 12,
            path="/",
            samesite="Lax"
        )
        
        print("Cookies establecidas, actualizando estado del usuario")
        
        # Resetear intentos fallidos en login exitoso
        usuario.intentos_fallidos = 0
        usuario.ultimo_acceso = auth_utils.get_current_datetime()
        db.commit()
        
        print("Login completado exitosamente")
        return response

    except Exception as e:
        print(f"Error en login: {str(e)}")
        return templates.TemplateResponse(
            "auth/login.html",
            {
                "request": request,
                "error": "Error en el proceso de login. Por favor, intente nuevamente."
            }
        )

@auth_router.get("/change-password", response_class=HTMLResponse)
async def change_password_page(
    request: Request
):
    # Obtener el token de las cookies
    access_token = request.cookies.get("access_token")
    if not access_token:
        return RedirectResponse(url="/auth/login", status_code=302)
        
    try:
        # Verificar el token
        payload = auth_utils.verify_access_token(access_token)
        return templates.TemplateResponse(
            "auth/change_password.html", 
            {"request": request}
        )
    except:
        return RedirectResponse(url="/auth/login", status_code=302)

@auth_router.post("/change-password")
async def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    access_token = request.cookies.get("access_token")
    session_data = request.cookies.get("session_data")
    
    if not access_token:
        raise HTTPException(status_code=401, detail="No autenticado")
        
    try:
        # Verificar el token
        payload = auth_utils.verify_access_token(access_token)
        
        # Obtener usuario
        usuario = db.query(Usuario).filter(
            Usuario.codigo == payload["sub"]
        ).first()
        
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
            
        # Verificar contraseña actual
        if not auth_utils.verify_password(current_password, usuario.password_hash):
            raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")
            
        # Verificar que las nuevas contraseñas coincidan
        if new_password != confirm_password:
            raise HTTPException(status_code=400, detail="Las contraseñas nuevas no coinciden")
            
        # Validar requisitos de la nueva contraseña
        if len(new_password) < 8:
            raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 8 caracteres")
            
        if new_password == current_password:
            raise HTTPException(status_code=400, detail="La nueva contraseña debe ser diferente a la actual")
            
        if new_password == usuario.codigo:
            raise HTTPException(status_code=400, detail="La contraseña no puede ser igual al código de usuario")
        
        # Actualizar contraseña
        usuario.password_hash = auth_utils.hash_password(new_password)
        usuario.requiere_cambio_password = False
        db.commit()
        
        # Crear nueva respuesta según tipo de usuario
        if usuario.tipo_usuario == "Comisión Cliente":
            redirect_url = "/dashboard/comision"
        elif usuario.tipo_usuario == "Inventariador Proveedor":
            redirect_url = "/dashboard/proveedor"
        elif usuario.tipo_usuario == "Gerencial Proveedor":
            redirect_url = "/dashboard/gerencial"
        else:
            redirect_url = "/demo-inventario"
            
        response = RedirectResponse(url=redirect_url, status_code=302)
        
        # Mantener las cookies de sesión
        if session_data:
            response.set_cookie(
                key="session_data",
                value=session_data,
                httponly=False,
                max_age=3600 * 12,
                path="/",
                samesite="Lax"
            )
        
        # Mantener el token de acceso
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=3600 * 12,
            secure=True,
            samesite="lax"
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@auth_router.post("/renew-session")
async def renew_session(request: Request):
    try:
        # Verificar token actual
        access_token = request.cookies.get("access_token")
        if not access_token:
            raise HTTPException(status_code=401, detail="No autenticado")
            
        # Renovar tanto el token como los datos de sesión
        session_data = request.cookies.get("session_data")
        if not session_data:
            raise HTTPException(status_code=401, detail="No autenticado")

        response = JSONResponse({"status": "ok"})
        
        # Renovar cookies con nuevo tiempo de expiración
        response.set_cookie(
            key="session_data",
            value=session_data,
            httponly=False,
            max_age=3600 * 12,  # 12 horas
            path="/",
            samesite="Lax"
        )
        
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=3600 * 12,  # 12 horas
            secure=True,
            samesite="Lax"
        )
        
        return response
    except Exception as e:
        raise HTTPException(status_code=401, detail="Error renovando sesión")

@auth_router.post("/logout")
async def logout():
    response = JSONResponse({"status": "ok"})
    response.delete_cookie("session_data")
    response.delete_cookie("access_token")
    return response