# routers/comision.py
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, aliased
from sqlalchemy import func, and_
from sqlalchemy.sql import text, literal_column
#from utils.kpi_calculations import get_inventory_analysis
#from utils.pdf_generator import generate_analysis_pdf
from typing import Dict
import json
from database import get_db
from sqlalchemy import func
from scripts.sql_alc.create_tables_BD_INVENTARIO import Bien, Sede, AsignacionBien, Usuario


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

# ****************************** CANTIDAD DE BINES POR DIA Y POR SEDE *************************

def bienes_avance_por_sede(db_session):
    """
    Consulta el avance del inventario agrupado por sede.
    """
    results = (
        db_session.query(
            Sede.id.label("sede_id"),
            Sede.nombre.label("sede"),
            Sede.cantidad_bienes.label("cantidad_bienes"),
            func.count(Bien.id).label("total_bienes"),
            func.count(AsignacionBien.id).label("bienes_inventariados"),
            (func.count(AsignacionBien.id) / func.count(Bien.id) * 100).label("porcentaje_avance"),
            (func.count(AsignacionBien.id) / func.count(func.date(AsignacionBien.fecha_asignacion))).label("promedio_diario")
        )
        .join(Bien, Bien.sede_actual_id == Sede.id)
        .outerjoin(AsignacionBien, Bien.id == AsignacionBien.bien_id)
        .group_by(Sede.id, Sede.nombre)
        .order_by(Sede.nombre)
        .all()
    )
    return [
        {
            "sede_id": r.sede_id,
            "sede": r.sede,
            "cantidad_bienes":r.cantidad_bienes,
            "total_bienes": r.total_bienes,
            "bienes_inventariados": r.bienes_inventariados,
            "porcentaje_avance": round(r.porcentaje_avance, 2) if r.porcentaje_avance else 0,
            "promedio_diario": round(r.promedio_diario, 2) if r.promedio_diario else 0,
        }
        for r in results
    ]

# ********************** DETALLES POR SEDE *************************
def ranking_inventariadores_por_sede(db_session, sede_id, institucion_id=None, fecha_inicio=None, fecha_fin=None):
    """
    Genera un ranking de bienes inventariados por cada inventariador en una sede,
    filtrando por un rango de fechas si se proporciona.
    """
    # Filtros básicos
    filtros = [Bien.sede_actual_id == sede_id ]

    # Filtro por institución
    if institucion_id:
        filtros.append(Bien.institucion_id == institucion_id)
    
    if fecha_inicio:
        filtros.append(Bien.fecha_hora >= fecha_inicio)
    if fecha_fin:
        filtros.append(Bien.fecha_hora <= fecha_fin)

    # Alias para la tabla usuarios
    UsuarioAlias = aliased(Usuario)  # Cambia `User` por el nombre de tu modelo para la tabla usuarios

    results = (
        db_session.query(
            UsuarioAlias.codigo.label("codigo_usuario"),
            UsuarioAlias.nombres.label("nombre"),
            UsuarioAlias.apellidos.label("apellidos"),
            UsuarioAlias.celular.label("telefono"),
            UsuarioAlias.id.label("inventariador_id"),
            func.count(Bien.id).label("bienes_inventariados"),
            (
                func.count(Bien.id) / 
                func.timestampdiff(
                    literal_column("HOUR"), 
                    func.min(Bien.fecha_hora), 
                    func.max(Bien.fecha_hora)
                )
            ).label("promedio_por_hora"),
        )
        .join(UsuarioAlias, UsuarioAlias.id == Bien.codigo_inventariador)  # Relación entre las tablas
        .filter(*filtros)
        .group_by(UsuarioAlias.id)
        .order_by(func.count(Bien.id).desc())
        .all()
    )

    return [
        {
            "codigo_usuario": row.codigo_usuario,
            "nombre": row.nombre,
            "apellidos": row.apellidos,
            "telefono": row.telefono,
            "bienes_inventariados": row.bienes_inventariados,
            "promedio_por_hora": round(row.promedio_por_hora, 2) if row.promedio_por_hora else 0,
        }
        for row in results
    ]
