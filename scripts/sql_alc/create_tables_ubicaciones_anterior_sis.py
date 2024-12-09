import os, sys
from pathlib import Path

# Añadir directorio raíz al path
root_path = str(Path(__file__).parent.parent.parent)
sys.path.append(root_path)

import sys, os
from pathlib import Path
from sqlalchemy import create_engine
import claves
from base_models import Base
from create_ubicaciones_fisicas import UbicacionFisica
from anterior_sis import AnteriorSis
from scripts.py.create_tables_BD_INVENTARIO import Sede, Oficina, Empleado
from sqlalchemy import Column, Integer, String, ForeignKey, Float, Text, MetaData
from sqlalchemy.orm import relationship, declarative_base

# Conexión a la base de datos
engine = create_engine(f"{os.getenv('DB_TYPE')}://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}")

# Crear Base usando el metadata existente
metadata = MetaData()
metadata.reflect(bind=engine)  # Esto carga las tablas existentes
Base = declarative_base(metadata=metadata)


class UbicacionFisica(Base):
    __tablename__ = 'ubicaciones_fisicas'
    id = Column(Integer, primary_key=True, autoincrement=True)
    sede_id = Column(Integer, ForeignKey('sedes.id'), nullable=False)
    oficina_id = Column(Integer, ForeignKey('oficinas.id'), nullable=False) 
    dependencia = Column(String(200), nullable=False)
    ambiente = Column(String(200))
    ubicacion = Column(String(50))

# scripts/sql_alc/create_anterior_sis.py
class AnteriorSis(Base):
        __tablename__ = 'anterior_sis'
        id = Column(Integer, primary_key=True, autoincrement=True)
        institucion_id = Column(Integer, nullable=True)
        item = Column(String(20))
        inv_2023 = Column(String(20))
        inv_2022 = Column(String(20))
        codigo_patrimonial = Column(String(20), unique=True)
        codigo_nacional = Column(String(20))
        descripcion = Column(String(200))
        marca = Column(String(100))
        modelo = Column(String(100))
        tipo = Column(String(100))
        material = Column(String(50), nullable=True)
        color = Column(String(50))
        numero_serie = Column(String(50))
        largo = Column(Float, nullable=True)
        ancho = Column(Float, nullable=True)
        alto = Column(Float, nullable=True)
        estado = Column(String(20))
        en_uso = Column(String(20))
        observaciones = Column(Text)
        num_placa = Column(String(50), nullable=True)
        anio_fabricac = Column(Integer, nullable=True)
        num_chasis = Column(String(100), nullable=True)
        num_motor = Column(String(100), nullable=True)
    
        # Relaciones
        empleado_id = Column(Integer, ForeignKey('empleados.id'))
        ubicacion_fisica_id = Column(Integer, ForeignKey('ubicaciones_fisicas.id'))
    
        empleado = relationship("Empleado")
        ubicacion = relationship("UbicacionFisica")

def crear_tablas():
    try:
        Base.metadata.create_all(engine)
        print("Tablas creadas exitosamente")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    crear_tablas()