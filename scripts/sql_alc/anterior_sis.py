from sqlalchemy import Column, Integer, String, ForeignKey, Float, Text, Boolean
from sqlalchemy.orm import relationship 
from .base_models import Base


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
   procedencia = Column(String(100), nullable=True)
   propietario = Column(String(100), nullable=True)
   faltante = Column(Boolean, default=True)
   sede_id = Column(Integer),
   sede =Column(String(50), nullable=True)
   ubicacion_actual =Column(String(300), nullable=True)
   
   # Relaciones
   empleado_id = Column(Integer, ForeignKey('empleados.id'))
   ubicacion_fisica_id = Column(Integer, ForeignKey('ubicaciones_fisicas.id'), nullable=True)
   
   empleado = relationship("Empleado")
   #ubicacion = relationship("UbicacionFisica")