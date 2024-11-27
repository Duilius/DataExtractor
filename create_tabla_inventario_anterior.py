from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, create_engine, func
)
from sqlalchemy.orm import declarative_base
from datetime import datetime
import os, claves

Base = declarative_base()

class InventarioAnterior(Base):
    __tablename__ = "inventario_anterior"

    id = Column(Integer, primary_key=True, autoincrement=True)
    institucion_id = Column(Integer, nullable=True)
    codigo_patrimonial = Column(String(50), nullable=True, unique=True)
    cod_ubicacion = Column(String(50), nullable=True)
    nombre_ubicacion = Column(String(100), nullable=True)
    descripcion = Column(Text, nullable=True)
    tipo = Column(String(50), nullable=True)
    material = Column(String(50), nullable=True)
    color = Column(String(50), nullable=True)
    largo = Column(Float, nullable=True)
    ancho = Column(Float, nullable=True)
    alto = Column(Float, nullable=True)
    marca = Column(String(50), nullable=True)
    modelo = Column(String(50), nullable=True)
    numero_serie = Column(String(100), nullable=True)
    estado = Column(String(50), nullable=True)
    en_uso = Column(Boolean, nullable=True)
    observaciones = Column(Text, nullable=True)
    codigo_usuario = Column(String(50), nullable=True)
    nombres_usuario = Column(String(100), nullable=True)
    area_usuario = Column(String(100), nullable=True)
    email_usuario = Column(String(100), nullable=True)
    celular_usuario = Column(String(20), nullable=True)
    codigo_nacional = Column(String(50), nullable=True)
    num_placa = Column(String(50), nullable=True)
    anio_fabricac = Column(Integer, nullable=True)
    num_chasis = Column(String(100), nullable=True)
    num_motor = Column(String(100), nullable=True)
    codigo_inv_2024 = Column(String(50), nullable=True)
    codigo_inv_2023 = Column(String(50), nullable=True)
    codigo_inv_2022 = Column(String(50), nullable=True)
    codigo_inv_2021 = Column(String(50), nullable=True)
    codigo_inv_2020 = Column(String(50), nullable=True)
    codigo_inv_2019 = Column(String(50), nullable=True)
    fecha_origen_data = Column(DateTime, default=func.now())
    origen_data = Column(String(100), nullable=True)
    observac_dex = Column(Text, nullable=True)
    observac_inventariador = Column(Text, nullable=True)

# Conexión a la base de datos
engine = create_engine(f"{os.getenv('DB_TYPE')}://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}")

Base.metadata.create_all(engine)
print("Tabla 'inventario_anterior' creada con éxito.")
