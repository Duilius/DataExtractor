# routers/comision.py
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, case
from sqlalchemy.orm import Session
from database import get_db
from scripts.sql_alc.create_tables_BD_INVENTARIO import Sede
from scripts.sql_alc.anterior_sis import AnteriorSis 

router = APIRouter(prefix="/dashboard/comision", tags=["comision"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def comision_dashboard(request: Request, db: Session = Depends(get_db)):
    """
    Vista principal del dashboard de comisión
    """
    # Mock de métricas para el dashboard
    metrics = {
        "avance_global": 45,
        "total_sedes": 10,
        "total_bienes": 1500,
        "total_inventariados": 675,
        "sedes": [
            {
                "id": 1,
                "nombre": "Sede Principal",
                "region": "Lima",
                "total_bienes": 500,
                "inventariados": 250,
                "pendientes": 250,
                "porcentaje": 50
            },
            # ... más sedes si necesitas
        ]
    }

    return templates.TemplateResponse(
        "dashboard/comision/index.html",
        {
            "request": request,
            "user": request.state.user,
            "metrics": metrics
        }
    )

@router.get("/analisis", response_class=HTMLResponse)
async def analisis_historico(request: Request, db: Session = Depends(get_db)):
    """
    Vista del análisis histórico
    """
    return templates.TemplateResponse(
        "dashboard/comision/comision.html",  # Usamos comision.html para el análisis
        {
            "request": request,
            "user": request.state.user
        }
    )

@router.get("/descargar-analisis")
async def descargar_analisis(request: Request, db: Session = Depends(get_db)):
    """
    Endpoint para descargar análisis en PDF
    """
    # Implementar generación de PDF
    pass


# routers/comision.py - Asegúrate que la ruta esté correcta
# routers/comision.py

@router.get("/analisis-historico", response_class=HTMLResponse)
async def analisis_historico(request: Request, db: Session = Depends(get_db)):
    """Vista del análisis histórico de inventarios"""
    try:
        from scripts.sql_alc.queries.hist_comparativo import get_comparativo_data
        
        # Obtener datos
        try:
            resumen_data = get_comparativo_data(db)
        except Exception as e:
            print(f"Error obteniendo datos comparativos: {str(e)}")
            resumen_data = {
                "total_comparison": {"labels": [], "data": []},
                "estado_2023": {"labels": [], "data": []},
                "por_sede": {"labels": [], "data_2022": [], "data_2023": []}
            }
        
        return templates.TemplateResponse(
            "dashboard/comision/analisis_historico.html",
            {
                "request": request,
                "user": request.state.user,
                "resumen_data": resumen_data,
                "compras_data": None,
                "bajas_data": None,
                "operativo_data": None
            }
        )
    except Exception as e:
        print(f"Error en análisis histórico: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return templates.TemplateResponse(
            "dashboard/comision/analisis_historico.html",
            {
                "request": request,
                "user": request.state.user,
                "error": "Error al cargar los datos del análisis",
                "resumen_data": None
            }
        )