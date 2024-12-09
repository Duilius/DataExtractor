from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from scripts.sql_alc.proveedor_stats import StatsService
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from database import get_db

proveedor_router = APIRouter()  # En vez de router = APIRouter()
templates = Jinja2Templates(directory="templates")

@proveedor_router.get("/dashboard/proveedor", response_class=HTMLResponse)
async def dashboard_proveedor(request: Request, db: Session = Depends(get_db)):
    stats_service = StatsService(db)

    sede_actual_id = request.session.get("user", {}).get("sede_actual_id")
    metrics = {
        "sede_info": {
            "id": sede_actual_id,
            "nombre": "Sede Actual",
            "provincia": "Provincia"
        },
        "porcentaje_avance": 65,
        "bienes_procesados": 150,
        "total_bienes": 200,
        "bienes_hoy": 25,
        "sin_etiqueta": 10
    }
    
    return templates.TemplateResponse("dashboard/proveedor/hybrid_index.html", {
        "request": request,
        "metrics": metrics,
        "user": {
            "sub": request.session.get("codigo", ""),  # Obtenemos el código de usuario
            # otros datos del usuario si necesitas
        }
    })

@proveedor_router.get("/dashboard/proveedor/stats/sede/{sede_id}")
async def get_sede_stats(sede_id: int, db: Session = Depends(get_db)):
    stats_service = StatsService(db)
    return await stats_service.get_sede_stats(sede_id)