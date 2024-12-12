from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sqlalchemy as sa
from typing import List
import logging
from contextlib import asynccontextmanager

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
import os, claves


engine = create_engine(f"{os.getenv('DB_TYPE')}://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}")


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def remove_columns():
    try:
        with engine.begin() as conn:
            # Eliminar la foreign key específica de asignaciones_bienes
            try:
                drop_fk = text("""
                    ALTER TABLE asignaciones_bienes
                    DROP FOREIGN KEY asignaciones_bienes_ibfk_3
                """)
                conn.execute(drop_fk)
                logger.info("Foreign key eliminada exitosamente de asignaciones_bienes")

                # Ahora intentamos eliminar la columna
                drop_column = text("""
                    ALTER TABLE asignaciones_bienes 
                    DROP COLUMN proceso_inventario_id
                """)
                conn.execute(drop_column)
                logger.info("Columna proceso_inventario_id eliminada exitosamente de asignaciones_bienes")
            except Exception as e:
                logger.info(f"Error con asignaciones_bienes: {str(e)}")
            
    except Exception as e:
        logger.error(f"Error durante la migración: {str(e)}")
        raise e

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando la aplicación...")
    try:
        remove_columns()
        logger.info("Migración completada exitosamente")
    except Exception as e:
        logger.error(f"Error durante el inicio de la aplicación: {str(e)}")
        logger.error("No se pudo completar la migración")
    
    yield
    
    try:
        engine.dispose()
        logger.info("Aplicación cerrada correctamente. Conexiones de base de datos liberadas.")
    except Exception as e:
        logger.error(f"Error durante el cierre de la aplicación: {str(e)}")

app = FastAPI(lifespan=lifespan)

@app.get("/migration-status")
async def get_migration_status():
    """
    Endpoint para verificar el estado de la migración
    """
    try:
        with engine.connect() as conn:
            inspector = sa.inspect(engine)
            
            # Verificar asignaciones_bienes
            columns_asignaciones = inspector.get_columns('asignaciones_bienes')
            asignaciones_exists = any(col['name'] == 'proceso_inventario_id' for col in columns_asignaciones)
            
            return {
                "success": True,
                "asignaciones_bienes": {
                    "message": "La columna proceso_inventario_id no existe" if not asignaciones_exists else "La columna proceso_inventario_id aún existe",
                    "column_exists": asignaciones_exists
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)