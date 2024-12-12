from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sqlalchemy as sa
from typing import List
import logging
from contextlib import asynccontextmanager
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
import os, claves


engine = create_engine(f"{os.getenv('DB_TYPE')}://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}")


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modelo para la tabla anterior_sis
class AnteriorSis(Base):
    __tablename__ = 'anterior_sis'
    
    id = Column(Integer, primary_key=True)
    codigo_dni = Column(String(8))  # Asumiendo que el DNI es de 8 dígitos
    # Añade aquí otros campos que necesites de la tabla
    
def get_bienes_by_dni(dni: str):
    """
    Consulta bienes por código DNI en la tabla anterior_sis
    """
    try:
        # Crear sesión
        db = SessionLocal()
        
        # Realizar la consulta
        bienes = db.query(AnteriorSis).filter(
            AnteriorSis.codigo_dni == dni
        ).all()
        
        # Log informativo
        logger.info(f"Se encontraron {len(bienes)} bienes para el DNI {dni}")
        
        return bienes
        
    except Exception as e:
        logger.error(f"Error al consultar bienes por DNI: {str(e)}")
        raise e
    
    finally:
        db.close()

def main():
    # Ejemplo de uso
    try:
        dni = input("Ingrese el DNI a consultar: ")
        bienes = get_bienes_by_dni(dni)
        
        if not bienes:
            print(f"No se encontraron bienes para el DNI {dni}")
            return
        
        print(f"\nBienes encontrados para DNI {dni}:")
        for bien in bienes:
            print(f"ID: {bien.id}")
            print(f"DNI: {bien.codigo_dni}")
            # Imprime aquí otros campos que necesites
            print("-" * 50)
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()