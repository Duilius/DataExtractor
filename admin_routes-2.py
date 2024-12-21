from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from scripts.py.user_operations import user_operations
from scripts.sql_alc.create_tables_BD_INVENTARIO import Institucion, Sede  # Importa las tablas relacionadas

admin_router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")

@admin_router.post("/usuarios/crear")
async def crear_usuario(
    request: Request,
    user_data: dict,
    db: Session = Depends(get_db)
):
    try:
        nuevo_usuario = user_operations.create_user(db, user_data)
        return {"mensaje": "Usuario creado exitosamente", "id": nuevo_usuario.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@admin_router.post("/usuarios/cambiar-sede")
async def cambiar_sede(
    request: Request,
    usuario_id: int,
    nueva_sede_id: int,
    db: Session = Depends(get_db)
):
    try:
        usuario = user_operations.cambiar_sede_usuario(db, usuario_id, nueva_sede_id)
        # Invalidar sesiones existentes del usuario
        # Esto forzará un nuevo login la próxima vez que el usuario intente acceder
        usuario.esta_activo = False
        db.commit()
        
        return {
            "mensaje": "Sede actualizada exitosamente. El usuario deberá iniciar sesión nuevamente.",
            "nueva_sede_id": nueva_sede_id
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@admin_router.get("/test-crear-usuario")
async def test_crear_usuario(db: Session = Depends(get_db)):
    # Primero verificar si existe la institución y sede
    institucion = db.query(Institucion).first()
    sede = db.query(Sede).first()
    
    if not institucion or not sede:
        return {"error": "No hay instituciones o sedes registradas"}

    user_data = {
        "codigo": "INV001",
        "email": "inventariador1@empresa.com",
        "tipo_usuario": "Inventariador Proveedor",
        "institucion_id": institucion.id,
        "sede_actual_id": sede.id
    }
    try:
        nuevo_usuario = user_operations.create_user(db, user_data)
        return {
            "mensaje": "Usuario creado exitosamente", 
            "id": nuevo_usuario.id,
            "institucion": institucion.id,
            "sede": sede.id
        }
    except Exception as e:
        return {"error": str(e)}