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

        # Verificar si la cuenta está activa
        if not usuario.esta_activo:
            print(f"Cuenta bloqueada: {codigo}")
            return templates.TemplateResponse(
                "auth/login.html",
                {
                    "request": request,
                    "error": "Cuenta bloqueada. Contacte al administrador"
                }
            )
        
        # Verificar contraseña
        if not auth_utils.verify_password(password, usuario.password_hash):
            usuario.intentos_fallidos += 1
            if usuario.intentos_fallidos >= 5:
                usuario.esta_activo = False
                print(f"Cuenta bloqueada por múltiples intentos: {codigo}")
                mensaje_error = "Cuenta bloqueada por múltiples intentos fallidos"
            else:
                print(f"Intento fallido #{usuario.intentos_fallidos} para {codigo}")
                mensaje_error = "Usuario o contraseña incorrectos"
            
            db.commit()
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

        # Verificar sesión activa - VERIFICACIÓN ESTRICTA
        try:
            auth_utils.cleanup_expired_sessions()
            if auth_utils.check_active_session(str(usuario.id)):
                print(f"Bloqueando inicio de sesión para {usuario.codigo}: sesión activa detectada")
                return templates.TemplateResponse(
                    "auth/login.html",
                    {
                        "request": request,
                        "error": "Ya existe una sesión activa. Por favor, cierre la sesión anterior o espere 15 minutos."
                    }
                )
        except Exception as e:
            print(f"Error verificando sesión: {str(e)}")
            return templates.TemplateResponse(
                "auth/login.html",
                {
                    "request": request,
                    "error": "Error verificando sesión. Por favor, intente nuevamente en unos minutos."
                }
            )

        # Si llegamos aquí, no hay sesión activa
        print(f"Iniciando nueva sesión para {usuario.codigo}")
        access_token = auth_utils.create_access_token(
            data={"sub": usuario.codigo, "type": usuario.tipo_usuario}
        )
        
        auth_utils.register_session(str(usuario.id), access_token)
        print("Credenciales válidas, sesión creada")

        # Crear datos de sesión para el cliente
        session_data = {
            "id": usuario.id,
            "codigo": usuario.codigo,
            "tipo_usuario": usuario.tipo_usuario,
            "institucion_id": usuario.institucion_id,
            "sede_actual_id": usuario.sede_actual_id
        }

        # Determinar la redirección según el tipo de usuario
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

        # Agregar trigger para verificación de sesión única
        response.headers["HX-Trigger"] = "check-single-session"

        # Establecer cookies
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=3600 * 12,
            secure=True,
            samesite="lax"
        )
        
        response.set_cookie(
            key="session_data",
            value=json.dumps(session_data),
            httponly=False,
            max_age=3600 * 12,
            path="/",
            samesite="Lax"
        )

        print("Cookies establecidas, actualizando estado del usuario")
        
        # Actualizar estado del usuario
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
            
        response = JSONResponse({"status": "success"})
        response.headers["HX-Redirect"] = redirect_url
                
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
        return JSONResponse(
            status_code=400,
            content={"error": str(e)}
        )

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
async def logout(request: Request):
    try:
        # Obtener el token y payload
        token = request.cookies.get("access_token")
        if token:
            payload = auth_utils.verify_access_token(token)
            user_id = str(payload.get("sub"))
            # Limpiar la sesión activa
            if user_id in auth_utils._active_sessions:
                del auth_utils._active_sessions[user_id]
    except:
        pass

    response = JSONResponse({"status": "ok"})
    response.delete_cookie("session_data")
    response.delete_cookie("access_token")
    return response


#******* rutas adicionales Jueves 5- Diciembre ***********
@auth_router.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    return templates.TemplateResponse("auth/forgot_password.html", {"request": request})

@auth_router.post("/forgot-password")
async def forgot_password(
    request: Request,
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario:
        reset_token = auth_utils.create_access_token(
            data={"sub": usuario.codigo, "action": "reset_password"},
            expires_delta=timedelta(hours=24)
        )
        # TODO: Implementar envío de email cuando tengas SMTP
        print(f"Reset token generado: {reset_token}")
        
    return templates.TemplateResponse(
        "auth/forgot_password.html",
        {
            "request": request,
            "message": "Si el correo existe, recibirás instrucciones para recuperar tu contraseña"
        }
    )

#********** NUEVAS RUTAS ==> Jueves 5 Diciembre ******************
# Agregar estos imports si no existen
from datetime import timedelta
from fastapi.responses import JSONResponse

@auth_router.post("/validate-token")
async def validate_reset_token(token: str):
    try:
        auth_utils.verify_access_token(token)
        return {"valid": True}
    except:
        return JSONResponse(
            status_code=400,
            content={"valid": False, "message": "Token inválido o expirado"}
        )

@auth_router.post("/check-password-strength")
async def check_password_strength(password: str = Form(...)):
    """Validación de contraseña en servidor"""
    errors = []
    if len(password) < 8:
        errors.append("Mínimo 8 caracteres")
    if not any(c.isupper() for c in password):
        errors.append("Debe contener mayúsculas")
    if not any(c.islower() for c in password):
        errors.append("Debe contener minúsculas")
    if not any(c.isdigit() for c in password):
        errors.append("Debe contener números")
    if not any(c in "!@#$%^&*(),.?\":{}|<>" for c in password):
        errors.append("Debe contener caracteres especiales")
        
    return {"valid": len(errors) == 0, "errors": errors}

@auth_router.get("/session-info")
async def get_session_info(request: Request):
    """Obtener información de la sesión actual"""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")
    
    try:
        payload = auth_utils.verify_access_token(token)
        return {
            "authenticated": True,
            "user_type": payload.get("type"),
            "expires": payload.get("exp")
        }
    except:
        raise HTTPException(status_code=401, detail="Sesión inválida")

@auth_router.post("/unlock-account")
async def unlock_account(
    codigo: str = Form(...),
    db: Session = Depends(get_db)
):
    """Desbloquear cuenta después de muchos intentos fallidos"""
    usuario = db.query(Usuario).filter(Usuario.codigo == codigo).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    usuario.esta_activo = True
    usuario.intentos_fallidos = 0
    db.commit()
    
    return {"message": "Cuenta desbloqueada exitosamente"}