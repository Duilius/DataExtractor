from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from database import get_db
from scripts.py.create_tables_BD_INVENTARIO import Sede, Dependencia, UnidadFuncional, Area

router = APIRouter()

@router.get("/ubicaciones")
async def obtener_ubicaciones(db: Session = Depends(get_db)):
    # Consultar todas las sedes con sus dependencias
    sedes = db.query(Sede).all()
    
    # Estructurar los datos para el selector
    ubicaciones = []
    for sede in sedes:
        sede_info = {
            "id": sede.id,
            "nombre": sede.nombre,
            "dependencias": []
        }
        
        # Obtener dependencias para esta sede
        dependencias = db.query(Dependencia).filter(Dependencia.sede_id == sede.id).all()
        
        for dependencia in dependencias:
            sede_info["dependencias"].append({
                "id": dependencia.id,
                "nombre": dependencia.nombre
            })
        
        ubicaciones.append(sede_info)
    
    return ubicaciones

@router.get("/selector-ubicaciones")
async def selector_ubicaciones(db: Session = Depends(get_db)):
    # Consultar todas las sedes con sus dependencias
    sedes = db.query(Sede).all()
    
    # Preparar opciones para el selector
    opciones = []
    for sede in sedes:
        dependencias = db.query(Dependencia).filter(Dependencia.sede_id == sede.id).all()
        
        opciones.append({
            "sede": {
                "id": sede.id,
                "nombre": sede.nombre
            },
            "dependencias": [
                {
                    "id": dep.id,
                    "nombre": dep.nombre,
                    "valor": f"{sede.id}_{dep.id}"
                } for dep in dependencias
            ]
        })
    
    return opciones