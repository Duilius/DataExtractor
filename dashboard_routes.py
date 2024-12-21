from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse,RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from sqlalchemy import func
#from scripts.sql_alc.auth_models import Usuario
from scripts.sql_alc.create_tables_BD_INVENTARIO import (
    Usuario,
    Bien, 
    InventarioBien, 
    ProcesoInventario,
    Sede,
    AsignacionBien
)
import json
from gerencial_routes import gerencial_router

dashboard_router = APIRouter(prefix="/dashboard", tags=["dashboard"])
dashboard_router.include_router(gerencial_router)
templates = Jinja2Templates(directory="templates")

async def get_proveedor_metrics(db: Session, user_data: dict):
    """Obtiene métricas para el dashboard del inventariador proveedor"""
    sede_id = user_data.get('sede_actual_id')
    
    # Obtener información de la sede actual
    sede = db.query(Sede).filter(Sede.id == sede_id).first()
    
    # Conteos generales de la sede
    total_bienes = sede.cantidad_bienes if sede else 0
    bienes_procesados = db.query(InventarioBien).join(Bien).filter(
        Bien.sede_actual_id == sede_id
    ).distinct(InventarioBien.bien_id).count()
    
    # Conteos del día para el inventariador
    bienes_hoy = db.query(InventarioBien).filter(
        func.date(InventarioBien.fecha_registro) == func.current_date()
    ).count()
    
    # Bienes sin etiqueta
    sin_etiqueta = db.query(Bien).filter(
        Bien.requiere_etiqueta == True,
        Bien.sede_actual_id == sede_id
    ).count()
    
    return {
        "sede_info": {
            "nombre": sede.nombre if sede else "No asignada",
            "region": sede.region,
            "provincia": sede.provincia,
            "distrito": sede.distrito
        },
        "total_bienes": total_bienes,
        "bienes_procesados": bienes_procesados,
        "porcentaje_avance": round((bienes_procesados/total_bienes * 100), 2) if total_bienes > 0 else 0,
        "bienes_hoy": bienes_hoy,
        "sin_etiqueta": sin_etiqueta
    }

@dashboard_router.get("/comision", response_class=HTMLResponse)
async def dashboard_comision(
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        # Obtener datos del usuario de la cookie de sesión
        session_data = request.cookies.get("session_data")
        if not session_data:
            return RedirectResponse(url="/auth/login", status_code=302)
            
        user_data = json.loads(session_data)
        
        if user_data.get("tipo_usuario") != "Comisión Cliente":
            raise HTTPException(status_code=403, detail="Acceso no autorizado")

        metrics = await get_comision_metrics(db, user_data)
        
        return templates.TemplateResponse(
            "dashboard/comision/index.html",
            {
                "request": request,
                "user": user_data,
                "metrics": metrics
            }
        )
    except Exception as e:
        print(f"Error en dashboard comision: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    

async def get_comision_metrics(db: Session, user_data: dict):
    """Obtiene métricas para el dashboard de la comisión"""
    institucion_id = user_data.get('institucion_id')
        
    # Obtener todas las sedes de la institución
    sedes = db.query(Sede).filter(Sede.institucion_id == institucion_id).all()
    
    sedes_metrics = []
    total_avance = 0
    
    for sede in sedes:
        # Bienes inventariados en esta sede
        bienes_inventariados = db.query(AsignacionBien).join(Bien).filter(
            Bien.sede_actual_id == sede.id
        ).distinct(InventarioBien.bien_id).count()
        
        # Calcular porcentaje de avance
        porcentaje = round((bienes_inventariados / sede.cantidad_bienes * 100), 2) if sede.cantidad_bienes > 0 else 0
        
        sedes_metrics.append({
            "id": sede.id,
            "nombre": sede.nombre,
            "region": sede.region,
            "total_bienes": sede.cantidad_bienes,
            "inventariados": bienes_inventariados,
            "porcentaje": porcentaje,
            "pendientes": sede.cantidad_bienes - bienes_inventariados
        })
        
        total_avance += porcentaje
    
    # Calcular avance global
    avance_global = round(total_avance / len(sedes), 2) if sedes else 0
    
    return {
        "sedes": sedes_metrics,
        "avance_global": avance_global,
        "total_sedes": len(sedes),
        "total_bienes": sum(sede.cantidad_bienes for sede in sedes),
        "total_inventariados": sum(sede["inventariados"] for sede in sedes_metrics)
    }

#ENDPOINT PARA GERENTES-PROVEEDOR

@dashboard_router.get("/gerencia", response_class=HTMLResponse)
async def dashboard_comision(
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        # Obtener datos del usuario de la cookie de sesión
        session_data = request.cookies.get("session_data")
        if not session_data:
            return RedirectResponse(url="/auth/login", status_code=302)
            
        user_data = json.loads(session_data)
        
        if user_data.get("tipo_usuario") != "Gerencial Proveedor":
            raise HTTPException(status_code=403, detail="Acceso no autorizado")

        return templates.TemplateResponse(
            "dashboard/gerencia/index.html",
            {
                "request": request
            }
        )
    except Exception as e:
        print(f"Error en dashboard comision: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))