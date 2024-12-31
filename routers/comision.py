# routers/comision.py
import json
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, case
from sqlalchemy.orm import Session
from database import get_db
from scripts.sql_alc.create_tables_BD_INVENTARIO import Sede
from scripts.sql_alc.anterior_sis import AnteriorSis 

# Importar las funciones de consulta
from scripts.sql_alc.queries.hist_comparativo import get_comparativo_data
from scripts.sql_alc.queries.hist_compras import get_compras_data
from scripts.sql_alc.queries.hist_bajas import get_bajas_data
from scripts.sql_alc.queries.hist_operativo import get_operativo_data

router = APIRouter(prefix="/dashboard/comision", tags=["comision"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def comision_dashboard(request: Request, db: Session = Depends(get_db)):
    """
    Vista principal del dashboard de comisión
    """

    # Obtener user de la cookie session_data
    session_data = request.cookies.get("session_data")
    user = json.loads(session_data) if session_data else None

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
            "user": user,
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
    try:
        from scripts.sql_alc.queries.hist_comparativo import get_comparativo_data
        from scripts.sql_alc.queries.hist_compras import get_compras_data
        from scripts.sql_alc.queries.hist_bajas import get_bajas_data
        from scripts.sql_alc.queries.hist_operativo import get_operativo_data
        
        resumen_data = get_comparativo_data(db)
        compras_data = get_compras_data(db)
        bajas_data = get_bajas_data(db)
        operativo_data = get_operativo_data(db)
        
        return templates.TemplateResponse(
            "dashboard/comision/analisis_historico.html",
            {
                "request": request,
                "user": request.state.user,
                "resumen_data": resumen_data,
                "compras_data": compras_data,
                "bajas_data": bajas_data,
                "operativo_data": None
            }
        )
    except Exception as e:
        print(f"Error en análisis histórico: {str(e)}")
        return templates.TemplateResponse(
            "dashboard/comision/analisis_historico.html",
            {
                "request": request,
                "user": request.state.user,
                "error": "Error al cargar los datos del análisis"
            }
        )
    

from fastapi.responses import FileResponse
from utils.pdf_generator import InformeInventarioPDF
from datetime import datetime
import os

@router.get("/descargar-analisis-pdf")
async def descargar_analisis_pdf(request: Request, db: Session = Depends(get_db)):
    """Genera y descarga el informe de análisis en PDF"""
    try:
        # Obtener todos los datos necesarios
        resumen_data = get_comparativo_data(db)
        compras_data = get_compras_data(db)
        bajas_data = get_bajas_data(db)
        operativo_data = get_operativo_data(db)

        # Generar el PDF
        generador_pdf = InformeInventarioPDF()
        pdf_buffer = generador_pdf.generar_informe(
            resumen_data, 
            compras_data, 
            bajas_data, 
            operativo_data
        )

        # Crear nombre de archivo con fecha
        fecha_actual = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"Analisis_Inventario_{fecha_actual}.pdf"
        
        # Guardar temporalmente el PDF
        ruta_temp = f"static/temp/{nombre_archivo}"
        os.makedirs("static/temp", exist_ok=True)
        
        with open(ruta_temp, "wb") as f:
            f.write(pdf_buffer.read())

        # Retornar el archivo
        return FileResponse(
            path=ruta_temp,
            filename=nombre_archivo,
            media_type="application/pdf",
            background=None  # Para que se descargue en lugar de mostrarse en el navegador
        )

    except Exception as e:
        print(f"Error generando PDF: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error generando el informe PDF"
        )