# routers/comision.py
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from utils.kpi_calculations import get_inventory_analysis
from utils.pdf_generator import generate_analysis_pdf
from typing import Dict
import json

router = APIRouter(prefix="/comision", tags=["comision"])
templates = Jinja2Templates(directory="templates")

@router.get("/analisis-historico", response_class=HTMLResponse)
async def analisis_historico(
    request: Request,
    db: Session = Depends(get_db)
):
    """Vista del análisis histórico de inventarios"""
    # Obtener datos de análisis
    analysis_data = await get_inventory_analysis(db)
    
    return templates.TemplateResponse(
        "dashboard/comision/analisis_historico.html",
        {
            "request": request,
            "data": analysis_data,
            "page_title": "Análisis Histórico de Inventarios"
        }
    )

@router.get("/descargar-analisis-pdf")
async def descargar_analisis_pdf(
    db: Session = Depends(get_db)
):
    """Genera y descarga el análisis en formato PDF"""
    analysis_data = await get_inventory_analysis(db)
    pdf_path = await generate_analysis_pdf(analysis_data)
    
    return FileResponse(
        pdf_path,
        filename="Analisis_Inventario.pdf",
        media_type="application/pdf"
    )

# Función auxiliar para obtener los datos del análisis
async def get_inventory_analysis(db: Session) -> Dict:
    """Recopila todos los datos de análisis"""
    return {
        "bienes_mantenimiento": await get_bienes_mantenimiento(db),
        "bienes_asegurables": await get_bienes_asegurables(db),
        "comparativo_inventario": await get_comparativo_inventario(db),
        "bienes_sin_uso": await get_bienes_sin_uso(db),
        "empleados_sin_puesto": await get_empleados_sin_puesto(db)
    }