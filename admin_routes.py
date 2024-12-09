from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from scripts.sql_alc.auth_models import Usuario
from scripts.py.auth_utils import AuthUtils
from database import get_db
from config import JWT_SECRET_KEY

admin_router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")
auth_utils = AuthUtils(JWT_SECRET_KEY)

@admin_router.get("/users", response_class=HTMLResponse)
async def list_users(
    request: Request,
    db: Session = Depends(get_db)
):
    usuarios = db.query(Usuario).all()
    return templates.TemplateResponse(
        "admin/users.html",
        {
            "request": request,
            "usuarios": usuarios
        }
    )

@admin_router.post("/reset-user/{codigo}")
async def reset_user(
    codigo: str,
    db: Session = Depends(get_db)
):
    usuario = db.query(Usuario).filter(Usuario.codigo == codigo).first()
    if usuario:
        usuario.password_hash = auth_utils.hash_password(usuario.codigo)
        usuario.requiere_cambio_password = True
        usuario.esta_activo = True
        usuario.intentos_fallidos = 0
        db.commit()
        return {"status": "success", "message": f"Clave reseteada para usuario {codigo}"}
    
    raise HTTPException(status_code=404, detail="Usuario no encontrado")