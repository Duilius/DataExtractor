from fastapi import APIRouter, Request, Depends, Query, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import get_db  # Asegúrate de tener una conexión a la base de datos
from scripts.sql_alc.create_tables_BD_INVENTARIO import Empleado
from scripts.py.buscar_por_trabajador_inventario import consulta_registro, consulta_area, consulta_codigo

#para los INDICADORES-GERENCIA
from utils.kpi_calculations import bienes_avance_por_sede, ranking_inventariadores_por_sede

templates = Jinja2Templates(directory="templates")

router = APIRouter(prefix="/dashboard/gerencia", tags=["Gerencia"])


@router.get("/", response_class=HTMLResponse)
async def gerencia_dashboard(request: Request):
    return templates.TemplateResponse("dashboard/gerencia.html", {"request": request, "year": 2024})


@router.get("/fichaLevInf/{empleado_id}", response_class=HTMLResponse)
async def ficha_levantamiento(
    empleado_id: int, request: Request, db: Session = Depends(get_db)
):
    # Consulta asignaciones
    query = text("""
        SELECT asignaciones_bienes.fecha_asignacion, bienes.codigo_inv_2024, bienes.codigo_inv_2023, bienes.codigo_patrimonial, bienes.codigo_nacional, bienes.descripcion, bienes.marca, bienes.modelo, bienes.numero_serie, bienes.color, bienes.observaciones_hallazgo, bienes.estado, bienes.en_uso, bienes.describe_area, bienes.acciones    
        FROM asignaciones_bienes
        JOIN bienes ON asignaciones_bienes.bien_id = bienes.id
        WHERE asignaciones_bienes.empleado_id = :empleado_id
    """)
    asignaciones = db.execute(query, {"empleado_id": empleado_id}).fetchall()

    # Consulta información del empleado
    empleado = db.execute(text("""
        SELECT nombre, puesto FROM empleados WHERE id = :empleado_id
    """), {"empleado_id": empleado_id}).fetchone()

    if not empleado:
        return HTMLResponse("Empleado no encontrado", status_code=404)

    # Convertir resultados a diccionarios
    empleado_dict = {"nombre": empleado[0], "puesto": empleado[1]}
    asignaciones_dict = [
        {
            "cod_inv_2024": a[1],
            "cod_inv_2023": a[2],
            "codigo_patrimonial": a[3],
            "codigo_nacional": a[4],
            "descripcion": a[5],
            "marca": a[6],
            "modelo": a[7],
            "numero_serie": a[8],
            "color": a[9],
            "observaciones": a[10],
            "estado": a[11],
            "en_uso": a[12],
            "ambiente": a[13],
            "acciones": a[14],

        }
        for a in asignaciones
    ]

    # Renderizar la plantilla
    return templates.TemplateResponse(
        "/dashboard/gerencia/fichaLevInf.html",
        {
            "request": request,
            "empleado": empleado_dict,
            "asignaciones": asignaciones_dict,
        },
    )


#PLANTILLA CON 2 OPCIONES PARA SELECCIONAR EMPLEADO
@router.get("/seleccionar-empleado", response_class=HTMLResponse)
async def seleccionar_empleado(request: Request):
    return templates.TemplateResponse(
        "dashboard/gerencia/seleccionar_empleado.html",
        {"request": request}
    )

#*********************** B Ú S Q U E D A  ----  IMPRESION FICHA LEVANT. INFORM ************************
# Endpoint para búsqueda por DNI o Apellidos
@router.post("/buscar-empleado",response_class=HTMLResponse)
async def buscar_empleado(request: Request, busca_usuario: str = Form(...), db: Session = Depends(get_db)):
    print("Se busca a : ====> ", busca_usuario)
    valor = busca_usuario
    users =consulta_registro(valor)
    print("Resultado =====>", users)
    return templates.TemplateResponse("/dashboard/gerencia/lista_empleados.html",{"request":request,"users":users})


#*********************** B Ú S Q U E D A  ----  NUEVO RESPONSABL DE BIEN ************************
# Endpoint para búsqueda por DNI o Apellidos
@router.post("/buscar-empleado2",response_class=HTMLResponse)
async def buscar_empleado(request: Request, buscando_nuevo_usuario: str = Form(...), db: Session = Depends(get_db)):
    print("Se busca a : ====> ", buscando_nuevo_usuario)
    valor = buscando_nuevo_usuario
    users =consulta_registro(valor)
    print("Resultado =====>", users)
    return templates.TemplateResponse("/demo/usuario_nuevo_seleccionado.html",{"request":request,"users":users})

# Endpoint para listar empleados por Sede
@router.get("/listar-empleados-sede", response_class=JSONResponse)
async def listar_empleados_sede(sede_id: int, db: Session = Depends(get_db)):
    """
    Listar empleados de una sede específica.
    """
    try:
        empleados = db.query(Empleado).filter(Empleado.sede_id == sede_id).all()
        if not empleados:
            return {"message": "No hay empleados en esta sede"}

        resultados = [{"id": emp.id, "nombre": emp.nombre, "dni": emp.codigo} for emp in empleados]
        return resultados
    except Exception as e:
        return {"error": str(e)}

# **************************************  INVENTARIO POR SEDES     **************************************
#router = APIRouter(prefix="/gerencia", tags=["Gerencia"])

@router.get("/kpis/bienes-dia-sede")
async def get_bienes_dia_sede(db: Session = Depends(get_db)):
    """
    Devuelve la cantidad de bienes inventariados por día y por sede.
    """
    data = bienes_avance_por_sede(db)  #EN utils.kpi_calculations
    return data

@router.get("/kpis", response_class=HTMLResponse)
async def kpis_view(request: Request, db: Session = Depends(get_db)):
    """
    Renderiza la vista de KPIs para gerencia.
    """
    data = bienes_avance_por_sede(db)
    return templates.TemplateResponse("dashboard/gerencia/kpis.html", {"request": request, "data": data})

#************************ DETALLES POR SEDE (al tocar una Sede en Avance por Sede)  *****************************
@router.get("/detalles/{sede_id}", response_class=HTMLResponse)
async def detalles_sede(
    sede_id: int, 
    request: Request,
    nombre: str = Query(None),
    codigo_usuario: str = Query(None), #Codigo Usuario Inventariador : COM001, INV001, GER001, ...
    cantidad_bienes: str = Query(None), #Cantidad TOTAL de Bienes en la Sede
    total_bienes: int = Query(None), 
    db: Session = Depends(get_db),
    fecha_inicio: str = Query(None),  # Fecha de inicio opcional
    fecha_fin: str = Query(None)      # Fecha de fin opcional
):
    """
    Muestra los detalles de bienes inventariados por inventariador en una sede,
    filtrados por un rango de fechas si se proporciona.
    """

    print("La Sede es ))))) > ", sede_id)
    # Llamar a la función utilitaria para obtener el ranking
    data = ranking_inventariadores_por_sede(db, sede_id, fecha_inicio, fecha_fin)
    print("la data ===========>", data)
    return templates.TemplateResponse(
        "/dashboard/gerencia/detalles_sede.html", 
        {
            "request": request,
            "data": data,
            "nombre_sede":nombre,
            "cantidad_bienes":cantidad_bienes,
            "codigo_usuario":codigo_usuario,
            "total_bienes":total_bienes,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
        }
    )
