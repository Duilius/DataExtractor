from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from scripts.sql_alc.create_tables_BD_INVENTARIO import Oficina

office_router = APIRouter(prefix="/api/offices")

@office_router.get("/{institucion_id}/{sede_id}")
async def get_offices(institucion_id: int, sede_id: int, db: Session = Depends(get_db)):
    try:
        offices = db.query(Oficina).filter(
            Oficina.institucion_id == institucion_id,
            Oficina.sede_id == sede_id
        ).all()
        
        return [{
            "id": office.id,
            "codigo": office.codigo,
            "nombre": office.nombre,
            "nivel": office.nivel
        } for office in offices]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))