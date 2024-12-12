from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from create_tables_BD_INVENTARIO import Dependencia, UnidadFuncional, Area

router = APIRouter()

@router.post("/crear_estructura")
def crear_estructura_organizativa(
    sede_id: int, 
    dependencias: list[str], 
    unidades_funcionales: dict[str, list[str]] = {},
    areas: dict[str, dict[str, list[str]]] = {},
    db: Session = Depends(get_db)
):
    """
    Crear estructura organizativa completa
    
    - Crea dependencias para una sede
    - Opcionalmente crea unidades funcionales por dependencia
    - Opcionalmente crea áreas por unidad funcional
    """
    try:
        # Crear dependencias
        dependencias_creadas = []
        for nombre_dependencia in dependencias:
            dependencia = Dependencia(sede_id=sede_id, nombre=nombre_dependencia)
            db.add(dependencia)
            dependencias_creadas.append(dependencia)
        
        # Crear unidades funcionales
        unidades_creadas = []
        for dependencia in dependencias_creadas:
            if dependencia.nombre in unidades_funcionales:
                for nombre_unidad in unidades_funcionales[dependencia.nombre]:
                    unidad = UnidadFuncional(
                        dependencia_id=dependencia.id, 
                        nombre=nombre_unidad
                    )
                    db.add(unidad)
                    unidades_creadas.append(unidad)
        
        # Crear áreas
        for dependencia in dependencias_creadas:
            if dependencia.nombre in areas:
                for unidad_nombre, areas_unidad in areas[dependencia.nombre].items():
                    unidad = next((u for u in unidades_creadas if u.nombre == unidad_nombre and u.dependencia_id == dependencia.id), None)
                    if unidad:
                        for nombre_area in areas_unidad:
                            area = Area(
                                unidad_funcional_id=unidad.id, 
                                nombre=nombre_area
                            )
                            db.add(area)
        
        db.commit()
        return {"mensaje": "Estructura organizativa creada exitosamente"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))