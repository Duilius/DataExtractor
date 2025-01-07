import json
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse,JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, case
from sqlalchemy.orm import Session
from database import get_db
from scripts.sql_alc.create_tables_BD_INVENTARIO import Sede, AltasSis2024, Empleado, BajasSis2024
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

    # Convertir los resultados a una lista de diccionarios
    bienes_serialized = [
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

    total = db.query(AltasSis2024).filter(AltasSis2024.fecha_alta.between("2024-01-01", "2024-12-31")).count()

    return templates.TemplateResponse(
        "/dashboard/inventariador/altas.html",
        {
            "request": request,
            "user": user,
            "bienes": bienes_serialized,  # Ahora los datos son serializables
            "total": total,
            "page": 1,
            "pages": (total // limit) + (1 if total % limit > 0 else 0)
        }
    )


@router.get("/bienes-altas-2024/data", response_class=HTMLResponse)
async def bienes_altas_2024_data(request: Request, page: int = 1, limit: int = 10, query: str = None, db: Session = Depends(get_db)):
    """
    Devuelve los datos de bienes dados de alta en 2024, con soporte para paginación y búsquedas.
    """
    offset = (page - 1) * limit

    # Filtrar por búsqueda si se proporciona un query
    base_query = db.query(
        AltasSis2024.codigo_patrimonial,
        AltasSis2024.codigo_sbn,
        AltasSis2024.denominacion,
        AltasSis2024.color,
        AltasSis2024.marca,
        AltasSis2024.modelo,
        AltasSis2024.numero_serie,
        Empleado.nombre.label("usuario"),
        Sede.nombre.label("sede")
    ).join(Empleado, AltasSis2024.dni == Empleado.codigo).join(Sede, AltasSis2024.sede_id == Sede.id)

    if query:
        base_query = base_query.filter(AltasSis2024.denominacion.ilike(f"%{query}%"))

    total = base_query.count()
    result = base_query.offset(offset).limit(limit).all()

    bienes_serialized = [
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
        for row in result
    ]

    return templates.TemplateResponse(
        "partials/altas_table_rows.html",
        {
            "request": request,
            "bienes": bienes_serialized,
            "page": page,
            "pages": (total // limit) + (1 if total % limit > 0 else 0),
            "total": total,
        }
    )


# Lógica para manejar datos cargados en local
# Al tocar una fila, se usa la información local para mostrar el modal en el frontend sin consultar al backend.


@router.post("/search-bienes", response_class=HTMLResponse)
async def search_bienes(request: Request, db: Session = Depends(get_db), ):
    """
    Busca bienes por criterios específicos.
    """
    form = await request.form()
    filter_by = form.get("filter")
    query = form.get("query")

    page = int(form.get("page", 1))
    limit = int(form.get("limit", 10))
    offset = (page - 1) * limit

    print("QUERY =========> ", query)
    print("FILTER BY  =========> ", filter_by)

    # Filtra los bienes según el criterio seleccionado
    if filter_by == "codigo_patrimonial":
        result = db.query(AltasSis2024).filter(AltasSis2024.codigo_patrimonial == query).offset(offset).limit(limit).all()
    elif filter_by == "codigo_sbn":
        result = db.query(AltasSis2024).filter(AltasSis2024.codigo_sbn == query).offset(offset).limit(limit).all()
    elif filter_by == "denominacion":
        result = db.query(AltasSis2024).filter(AltasSis2024.denominacion.ilike(f"%{query}%")).offset(offset).limit(limit).all()
    elif filter_by == "numero_serie":
        result = db.query(AltasSis2024).filter(AltasSis2024.numero_serie == query).offset(offset).limit(limit).all()
    else:
        result = []

     # Serializar los resultados para que sean JSON serializable
    bienes_serialized = [
        {
            "codigo_patrimonial": row.codigo_patrimonial,
            "codigo_sbn": row.codigo_sbn,
            "denominacion": row.denominacion,
            "color": row.color,
            "marca": row.marca,
            "modelo": row.modelo,
            "numero_serie": row.numero_serie,
        }
        for row in result
    ]

    total = db.query(AltasSis2024).filter(AltasSis2024.denominacion.ilike(f"%{query}%")).count() if filter_by == "denominacion" else len(result)

    if total >= 1:

        return templates.TemplateResponse(
            "partials/altas_table_rows.html",
            {
                "request": request,
                "bienes": bienes_serialized,
                "page": page,
                "pages": (total // limit) + (1 if total % limit > 0 else 0),
                "total": total,
            }
        )
    else:
        return templates.TemplateResponse("partials/no_results.html", {"request": request})


#************************** BAJAS SIS 2024 ******************** BAJAS SIS 2024 ***************************

# Añadir estas rutas al inventariador.py

@router.get("/bienes-bajas-2024", response_class=HTMLResponse)
async def bienes_bajas_2024(request: Request, db: Session = Depends(get_db)):
    """
    Renderiza la página de bajas de bienes del 2024 con las primeras filas ya cargadas.
    """
    session_data = request.cookies.get("session_data")
    user = json.loads(session_data) if session_data else None

    # Cargar las primeras filas (página 1, 10 elementos por defecto)
    limit = 10
    query = (
        db.query(
            BajasSis2024.inv_2023,
            BajasSis2024.codigo_cp,
            BajasSis2024.codigo_sbn,
            BajasSis2024.denominacion,
            BajasSis2024.marca,
            BajasSis2024.modelo,
            BajasSis2024.color,
            BajasSis2024.medidas,
            BajasSis2024.num_serie,
            BajasSis2024.procedencia,
            BajasSis2024.dependencia,
            Empleado.nombre.label("usuario"),
            Sede.nombre.label("sede")
        )
        .join(Empleado, BajasSis2024.dni == Empleado.codigo)
        .join(Sede, BajasSis2024.sede_id == Sede.id)
        .limit(limit)
        .all()
    )

    # Convertir los resultados a una lista de diccionarios
    bienes_serialized = [
        {
            "inv_2023": row.inv_2023,
            "codigo_cp": row.codigo_cp,
            "codigo_sbn": row.codigo_sbn,
            "denominacion": row.denominacion,
            "marca": row.marca,
            "modelo": row.modelo,
            "color": row.color,
            "medidas": row.medidas,
            "num_serie": row.num_serie,
            "procedencia": row.procedencia,
            "dependencia": row.dependencia,
            "usuario": row.usuario,
            "sede": row.sede,
        }
        for row in query
    ]

    total = db.query(BajasSis2024).count()

    return templates.TemplateResponse(
        "/dashboard/inventariador/bajas.html",
        {
            "request": request,
            "user": user,
            "bienes": bienes_serialized,
            "total": total,
            "page": 1,
            "pages": (total // limit) + (1 if total % limit > 0 else 0)
        }
    )


@router.get("/bienes-bajas-2024/data", response_class=HTMLResponse)
async def bienes_bajas_2024_data(request: Request, page: int = 1, limit: int = 10, query: str = None, db: Session = Depends(get_db)):
    """
    Devuelve los datos de bienes dados de baja en 2024, con soporte para paginación y búsquedas.
    """
    offset = (page - 1) * limit

    # Consulta base
    base_query = db.query(
        BajasSis2024.inv_2023,
        BajasSis2024.codigo_cp,
        BajasSis2024.codigo_sbn,
        BajasSis2024.denominacion,
        BajasSis2024.marca,
        BajasSis2024.modelo,
        BajasSis2024.color,
        BajasSis2024.medidas,
        BajasSis2024.num_serie,
        BajasSis2024.procedencia,
        BajasSis2024.dependencia,
        Empleado.nombre.label("usuario"),
        Sede.nombre.label("sede")
    ).join(Empleado, BajasSis2024.dni == Empleado.codigo).join(Sede, BajasSis2024.sede_id == Sede.id)

    if query:
        base_query = base_query.filter(BajasSis2024.denominacion.ilike(f"%{query}%"))

    total = base_query.count()
    result = base_query.offset(offset).limit(limit).all()

    bienes_serialized = [
        {
            "inv_2023": row.inv_2023,
            "codigo_cp": row.codigo_cp,
            "codigo_sbn": row.codigo_sbn,
            "denominacion": row.denominacion,
            "marca": row.marca,
            "modelo": row.modelo,
            "color": row.color,
            "medidas": row.medidas,
            "num_serie": row.num_serie,
            "procedencia": row.procedencia,
            "dependencia": row.dependencia,
            "usuario": row.usuario,
            "sede": row.sede,
        }
        for row in result
    ]

    return templates.TemplateResponse(
        "partials/bajas_table_rows.html",
        {
            "request": request,
            "bienes": bienes_serialized,
            "page": page,
            "pages": (total // limit) + (1 if total % limit > 0 else 0),
            "total": total,
        }
    )


@router.post("/search-bienes-bajas", response_class=HTMLResponse)
async def search_bienes_bajas(request: Request, db: Session = Depends(get_db)):
    """
    Busca bienes de baja por criterios específicos.
    """
    form = await request.form()
    filter_by = form.get("filter")
    query = form.get("query")

    page = int(form.get("page", 1))
    limit = int(form.get("limit", 10))
    offset = (page - 1) * limit

    # Filtra los bienes según el criterio seleccionado
    if filter_by == "codigo_cp":
        result = db.query(BajasSis2024).filter(BajasSis2024.codigo_cp == query).offset(offset).limit(limit).all()
    elif filter_by == "codigo_sbn":
        result = db.query(BajasSis2024).filter(BajasSis2024.codigo_sbn == query).offset(offset).limit(limit).all()
    elif filter_by == "denominacion":
        result = db.query(BajasSis2024).filter(BajasSis2024.denominacion.ilike(f"%{query}%")).offset(offset).limit(limit).all()
    elif filter_by == "numero_serie":
        result = db.query(BajasSis2024).filter(BajasSis2024.num_serie == query).offset(offset).limit(limit).all()
    else:
        result = []

    # Serializar resultados
    bienes_serialized = [
        {
            "inv_2023": row.inv_2023,
            "codigo_cp": row.codigo_cp,
            "codigo_sbn": row.codigo_sbn,
            "denominacion": row.denominacion,
            "marca": row.marca,
            "modelo": row.modelo,
            "color": row.color,
            "medidas": row.medidas,
            "num_serie": row.num_serie,
            "procedencia": row.procedencia,
            "dependencia": row.dependencia,
        }
        for row in result
    ]

    total = db.query(BajasSis2024).filter(BajasSis2024.denominacion.ilike(f"%{query}%")).count() if filter_by == "denominacion" else len(result)

    if total >= 1:
        return templates.TemplateResponse(
            "partials/bajas_table_rows.html",
            {
                "request": request,
                "bienes": bienes_serialized,
                "page": page,
                "pages": (total // limit) + (1 if total % limit > 0 else 0),
                "total": total,
            }
        )
    else:
        return templates.TemplateResponse("partials/no_results.html", {"request": request})
    
# ****************** CONSULTAS DE PERSONAL ****************** CONSULTAS DE PERSONAL ***************************
@router.get("/consulta-personal", response_class=HTMLResponse)
async def consulta_personal(request: Request, db: Session = Depends(get_db)):
    """
    Renderiza la página de consulta de personal con las primeras filas cargadas.
    """
    session_data = request.cookies.get("session_data")
    user = json.loads(session_data) if session_data else None

    # Cargar las primeras filas (página 1, 10 elementos por defecto)
    limit = 10
    query = (
    db.query(
        Empleado.codigo,
        Empleado.nombre,
        Empleado.puesto,
        Empleado.rol,
        Sede.nombre.label("sede")
    )
        .join(Sede, Empleado.sede_id == Sede.id)
        .limit(limit)
        .all()
    )


    # Convertir los resultados a una lista de diccionarios
    empleados_serialized = [
    {
        "codigo": row.codigo,
        "nombre": row.nombre,
        "puesto": row.puesto,
        "rol": row.rol,
        "sede": row.sede
    }
        for row in query
    ]

    total = db.query(Empleado).count()

    return templates.TemplateResponse(
        "/dashboard/inventariador/consulta_personal.html",
        {
            "request": request,
            "user": user,
            "empleados": empleados_serialized,
            "total": total,
            "page": 1,
            "pages": (total // limit) + (1 if total % limit > 0 else 0)
        }
    )


@router.get("/consulta-personal/data", response_class=HTMLResponse)
async def consulta_personal_data(request: Request, page: int = 1, limit: int = 10, query: str = None, db: Session = Depends(get_db)):
    """
    Devuelve los datos de empleados, con soporte para paginación y búsquedas.
    """
    offset = (page - 1) * limit

    base_query = db.query(
        Empleado.codigo,
        Empleado.nombre,
        Empleado.email,
        Empleado.puesto,
        Empleado.rol,
        Sede.nombre.label("sede")
    ).join(Sede, Empleado.sede_id == Sede.id)

    if query:
        base_query = base_query.filter(Empleado.nombre.ilike(f"%{query}%"))

    total = base_query.count()
    result = base_query.offset(offset).limit(limit).all()

    empleados_serialized = [
        {
            "codigo": row.codigo,
            "nombre": row.nombre,
            "email": row.email,
            "puesto": row.puesto,
            "rol": row.rol,
            "sede": row.sede
        }
        for row in result
    ]

    return templates.TemplateResponse(
        "partials/consulta_personal_rows.html",
        {
            "request": request,
            "empleados": empleados_serialized,
            "page": page,
            "pages": (total // limit) + (1 if total % limit > 0 else 0),
            "total": total,
        }
    )


@router.post("/search-personal", response_class=HTMLResponse)
async def search_personal(request: Request, db: Session = Depends(get_db)):
    """
    Busca empleados por criterios específicos.
    """
    form = await request.form()
    filter_by = form.get("filter")
    query = form.get("query")

    page = int(form.get("page", 1))
    limit = int(form.get("limit", 10))
    offset = (page - 1) * limit

    # Filtra los empleados según el criterio seleccionado
    base_query = db.query(
        Empleado.codigo,
        Empleado.nombre,
        Empleado.email,
        Empleado.puesto,
        Empleado.rol,
        Sede.nombre.label("sede")
    ).join(Sede, Empleado.sede_id == Sede.id)

    if filter_by == "codigo":
        base_query = base_query.filter(Empleado.codigo == query)
    elif filter_by == "nombre":
        base_query = base_query.filter(Empleado.nombre.ilike(f"%{query}%"))
    elif filter_by == "email":
        base_query = base_query.filter(Empleado.email.ilike(f"%{query}%"))
    elif filter_by == "sede":
        base_query = base_query.join(Sede).filter(Sede.nombre.ilike(f"%{query}%"))

    result = base_query.offset(offset).limit(limit).all()
    total = base_query.count()

    empleados_serialized = [
        {
            "codigo": row.codigo,
            "nombre": row.nombre,
            "email": row.email,
            "puesto": row.puesto,
            "rol": row.rol,
            "sede": row.sede
        }
        for row in result
    ]

    if total >= 1:
        return templates.TemplateResponse(
            "partials/consulta_personal_rows.html",
            {
                "request": request,
                "empleados": empleados_serialized,
                "page": page,
                "pages": (total // limit) + (1 if total % limit > 0 else 0),
                "total": total,
            }
        )
    else:
        return templates.TemplateResponse("partials/no_results.html", {"request": request})
    

# ********************* SEDE - EMPLEADO ===> FICHA LEVANTAMIENTO INFO **************************
# Importar OrderBy si no está importado
from sqlalchemy import func, case, asc

@router.get("/sede-empleado", response_class=HTMLResponse)
async def sede_empleado(request: Request, db: Session = Depends(get_db)):
    """
    Vista para seleccionar sede y empleado
    """
    session_data = request.cookies.get("session_data")
    user = json.loads(session_data) if session_data else None

    # Obtener sedes filtradas y ordenadas
    sedes = (db.query(
        Sede.id,
        Sede.nombre,
        Sede.region,
        Sede.provincia,
        Sede.distrito
    )
    .filter(Sede.institucion_id == 17)
    .order_by(
        Sede.region,
        Sede.provincia,
        Sede.distrito
    )
    .all())
    
    return templates.TemplateResponse(
        "/dashboard/inventariador/sede_empleado.html",
        {
            "request": request,
            "user": user,
            "sedes": sedes
        }
    )

@router.get("/sede-empleado/empleados/{sede_id}", response_class=HTMLResponse)
async def get_empleados_sede(request: Request, sede_id: int, page: int = 1, query: str = None, db: Session = Depends(get_db)):
    """
    Obtiene los empleados de una sede específica con paginación
    """
    limit = 10
    offset = (page - 1) * limit

    # Query base
    base_query = db.query(
        Empleado.id,
        Empleado.codigo,
        Empleado.nombre,
        Empleado.puesto
    ).filter(Empleado.sede_id == sede_id)

    # Aplicar búsqueda si existe
    if query:
        base_query = base_query.filter(Empleado.nombre.ilike(f"%{query}%"))

    # Obtener total y resultados paginados
    total = base_query.count()
    empleados = base_query.offset(offset).limit(limit).all()

    empleados_serialized = [
        {
            "id": emp.id,
            "codigo": emp.codigo,
            "nombre": emp.nombre,
            "puesto": emp.puesto
        }
        for emp in empleados
    ]

    return templates.TemplateResponse(
        "partials/empleados_sede_rows.html",
        {
            "request": request,
            "empleados": empleados_serialized,
            "total": total,
            "page": page,
            "pages": (total // limit) + (1 if total % limit > 0 else 0)
        }
    )