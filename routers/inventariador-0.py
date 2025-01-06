import json
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse,JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, case
from sqlalchemy.orm import Session
from database import get_db
from scripts.sql_alc.create_tables_BD_INVENTARIO import Sede, AltasSis2024, Empleado
from scripts.sql_alc.anterior_sis import AnteriorSis 


router = APIRouter(prefix="/dashboard/inventariador", tags=["inventariador"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def comision_dashboard(request: Request, db: Session = Depends(get_db)):
    """
    Vista principal del dashboard de comisión
    """

    # Obtener user de la cookie session_data
    session_data = request.cookies.get("session_data")
    user = json.loads(session_data) if session_data else None

    return templates.TemplateResponse(
        "dashboard/inventariador/index.html",
        {
            "request": request,
            "user": user
        }
    )

# ***************************** Opción ==> bienes-alta-2024 ****************************
@router.get("/bienes-altas-2024", response_class=HTMLResponse)
async def bienes_altas_2024(request: Request, db: Session = Depends(get_db)):
    """
    Renderiza la página de altas de bienes del 2024 con las primeras filas ya cargadas.
    """
    session_data = request.cookies.get("session_data")
    user = json.loads(session_data) if session_data else None

    # Cargar las primeras filas (página 1, 10 elementos por defecto)
    limit = 10
    query = (
        db.query(
            AltasSis2024.codigo_patrimonial,
            AltasSis2024.codigo_sbn,
            AltasSis2024.denominacion,
            AltasSis2024.color,
            AltasSis2024.marca,
            AltasSis2024.modelo,
            AltasSis2024.numero_serie,
            Empleado.nombre.label("usuario"),
            Sede.nombre.label("sede")
        )
        .join(Empleado, AltasSis2024.dni == Empleado.codigo)
        .join(Sede, AltasSis2024.sede_id == Sede.id)
        .filter(AltasSis2024.fecha_alta.between("2024-01-01", "2024-12-31"))
        .limit(limit)
        .all()
    )

    total = db.query(AltasSis2024).filter(AltasSis2024.fecha_alta.between("2024-01-01", "2024-12-31")).count()

    return templates.TemplateResponse(
        "/dashboard/inventariador/altas.html",
        {
            "request": request,
            "user": user,
            "bienes": query,
            "total": total,
            "page": 1,
            "pages": (total // limit) + (1 if total % limit > 0 else 0),
            "count": total
        }
    )

@router.get("/bienes-altas-2024/data", response_class=JSONResponse)
async def bienes_altas_2024_data(page: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    """
    Devuelve los datos de bienes dados de alta en 2024, paginados.
    """
    offset = (page - 1) * limit
    query = (
        db.query(
            AltasSis2024.codigo_patrimonial,
            AltasSis2024.codigo_sbn,
            AltasSis2024.denominacion,
            AltasSis2024.color,
            AltasSis2024.marca,
            AltasSis2024.modelo,
            AltasSis2024.numero_serie,
            Empleado.nombre.label("usuario"),
            Sede.nombre.label("sede")
        )
        .join(Empleado, AltasSis2024.dni == Empleado.codigo)
        .join(Sede, AltasSis2024.sede_id == Sede.id)
        .filter(AltasSis2024.fecha_alta.between("2024-01-01", "2024-12-31"))
        .offset(offset)
        .limit(limit)
        .all()
    )

    total = db.query(AltasSis2024).filter(AltasSis2024.fecha_alta.between("2024-01-01", "2024-12-31")).count()

    # Convertir objetos a serializable
    data = [
        {
            "codigo_patrimonial": row.codigo_patrimonial,
            "codigo_sbn": row.codigo_sbn,
            "denominacion": row.denominacion,
            "color": row.color,
            "marca": row.marca,
            "modelo": row.modelo,
            "numero_serie": row.numero_serie,
            "usuario": row.usuario,
            "sede": row.sede,
        }
        for row in query
    ]

    return {
        "data": data,
        "total": total,
        "page": page,
        "pages": (total // limit) + (1 if total % limit > 0 else 0),
        "count":total
    }


@router.get("/bienes-altas-2024/details/{codigo_patrimonial}", response_class=JSONResponse)
async def bien_detalle(codigo_patrimonial: str, db: Session = Depends(get_db)):
    """
    Devuelve los detalles completos de un bien dado su código patrimonial.
    """
    elBien = (
        db.query(AltasSis2024)
        .filter(AltasSis2024.codigo_patrimonial == codigo_patrimonial)
        .first()
    )

    if not elBien:
        return JSONResponse(content={"error": "Bien no encontrado"}, status_code=404)

    return {
        "codigo_patrimonial": elBien.codigo_patrimonial,
        "codigo_sbn": elBien.codigo_sbn,
        "denominacion": elBien.denominacion,
        "color": elBien.color,
        "marca": elBien.marca,
        "modelo": elBien.modelo,
        "numero_serie": elBien.numero_serie,
        "caracteristicas": elBien.caracteristicas,
        "estado": elBien.estado,
        "situacion": elBien.situacion,
        "usuario": elBien.usuario,
        "dependencia": elBien.dependencia,
        "ambiente": elBien.ambiente,
        "sede": elBien.sede,
        "procedencia": elBien.procedencia,
        "propietario": elBien.propietario,
        "faltante": elBien.faltante,
        "oficina": elBien.oficina,
        "observacion": elBien.observacion,
        "documento_alta": elBien.documento_alta,
        "fecha_alta": elBien.fecha_alta
    }


@router.post("/search-bienes", response_class=HTMLResponse)
async def search_bienes(request: Request, db: Session = Depends(get_db), ):
    """
    Busca bienes por criterios específicos.
    """
    form = await request.form()
    filter_by = form.get("filter")
    query = form.get("query")

    print("QUERY =========> ", query)
    print("FILTER BY  =========> ", filter_by)

    # Filtra los bienes según el criterio seleccionado
    if filter_by == "codigo_patrimonial":
        result = db.query(AltasSis2024).filter(AltasSis2024.codigo_patrimonial == query).all()
    elif filter_by == "codigo_sbn":
        result = db.query(AltasSis2024).filter(AltasSis2024.codigo_sbn == query).all()
    elif filter_by == "denominacion":
        result = db.query(AltasSis2024).filter(AltasSis2024.denominacion.ilike(f"%{query}%")).all()
    elif filter_by == "numero_serie":
        result = db.query(AltasSis2024).filter(AltasSis2024.numero_serie == query).all()
    else:
        result = []

    count = len(result)

     # Si un solo resultado, renderiza el modal
     # Decidir respuesta
    if count == 1:
        return templates.TemplateResponse("partials/table_rows.html", {"request": request, "bien": result[0],"count":count } )
    elif count > 1:
        return templates.TemplateResponse("partials/table_rows.html", {"request": request, "bienes": result,"count":count } )
    else:
        return templates.TemplateResponse("partials/no_results.html", {"request": request,"count":count } )
