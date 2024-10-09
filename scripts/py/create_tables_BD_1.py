from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Enum, Date, Float, Boolean, DateTime
from sqlalchemy.orm import declarative_base, relationship
import enum

import os
import claves

## Variables de conexión a Base de Datos en Railway
db_user=os.getenv("DB_USER")
db_password=os.getenv("DB_PASSWORD")
db_host=os.getenv("DB_HOST")
db_port=os.getenv("DB_PORT")
db_name=os.getenv("DB_NAME")
db_type=os.getenv("DB_TYPE")

engine = create_engine(f'{db_type}://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')

Base = declarative_base()

class NivelJerarquico(enum.Enum):
    NIVEL_1 = 1
    NIVEL_2 = 2
    NIVEL_3 = 3

class TipoBien(enum.Enum):
    MUEBLE = "Mueble"
    ARTEFACTO = "Artefacto"

class TipoMovimiento(enum.Enum):
    ASIGNACION = "Asignación"
    PRESTAMO = "Préstamo"
    REPARACION = "Reparación"

class Institucion(Base):
    __tablename__ = 'instituciones'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    ruc = Column(String(20), unique=True, nullable=False)

class Sede(Base):
    __tablename__ = 'sedes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    institucion_id = Column(Integer, ForeignKey('instituciones.id'), nullable=False)
    nombre = Column(String(100), nullable=False)
    direccion = Column(String(255))
    
    institucion = relationship("Institucion", back_populates="sedes")

class Oficina(Base):
    __tablename__ = 'oficinas'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sede_id = Column(Integer, ForeignKey('sedes.id'), nullable=False)
    codigo = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    nivel = Column(Enum(NivelJerarquico), nullable=False)
    jefe_id = Column(Integer, ForeignKey('empleados.id'))
    oficina_superior_id = Column(Integer, ForeignKey('oficinas.id'), nullable=True)
    
    sede = relationship("Sede", back_populates="oficinas")
    jefe = relationship("Empleado", back_populates="oficina_dirigida")
    oficina_superior = relationship("Oficina", remote_side=[id], back_populates="oficinas_dependientes")
    oficinas_dependientes = relationship("Oficina", back_populates="oficina_superior")
    empleados = relationship("Empleado", back_populates="oficina")

class Empleado(Base):
    __tablename__ = 'empleados'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    institucion_id = Column(Integer, ForeignKey('instituciones.id'), nullable=False)
    codigo = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    oficina_id = Column(Integer, ForeignKey('oficinas.id'))
    es_inventariador = Column(Boolean, default=False)
    
    institucion = relationship("Institucion", back_populates="empleados")
    oficina = relationship("Oficina", back_populates="empleados")
    oficina_dirigida = relationship("Oficina", back_populates="jefe", uselist=False)
    bienes_responsable = relationship("MovimientoBien", back_populates="empleado_responsable")

class Bien(Base):
    __tablename__ = 'bienes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    institucion_id = Column(Integer, ForeignKey('instituciones.id'), nullable=False)
    codigo_patrimonial = Column(String(50), unique=True, nullable=False)
    descripcion = Column(String(255), nullable=False)
    tipo = Column(Enum(TipoBien), nullable=False)
    material = Column(String(100))
    color = Column(String(50))
    largo = Column(Float)
    ancho = Column(Float)
    alto = Column(Float)
    marca = Column(String(100))
    modelo = Column(String(100))
    numero_serie = Column(String(100))
    
    institucion = relationship("Institucion", back_populates="bienes")
    movimientos = relationship("MovimientoBien", back_populates="bien")
    inventarios = relationship("InventarioBien", back_populates="bien")

class MovimientoBien(Base):
    __tablename__ = 'movimientos_bienes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    bien_id = Column(Integer, ForeignKey('bienes.id'), nullable=False)
    empleado_id = Column(Integer, ForeignKey('empleados.id'), nullable=False)
    sede_origen_id = Column(Integer, ForeignKey('sedes.id'), nullable=False)
    sede_destino_id = Column(Integer, ForeignKey('sedes.id'), nullable=False)
    tipo_movimiento = Column(Enum(TipoMovimiento), nullable=False)
    fecha_desde = Column(DateTime, nullable=False)
    fecha_hasta = Column(DateTime)
    
    bien = relationship("Bien", back_populates="movimientos")
    empleado_responsable = relationship("Empleado", back_populates="bienes_responsable")
    sede_origen = relationship("Sede", foreign_keys=[sede_origen_id])
    sede_destino = relationship("Sede", foreign_keys=[sede_destino_id])

class ProcesoInventario(Base):
    __tablename__ = 'procesos_inventario'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    institucion_id = Column(Integer, ForeignKey('instituciones.id'), nullable=False)
    anio = Column(Integer, nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date)
    
    institucion = relationship("Institucion", back_populates="procesos_inventario")

class InventarioBien(Base):
    __tablename__ = 'inventarios_bienes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    bien_id = Column(Integer, ForeignKey('bienes.id'), nullable=False)
    proceso_inventario_id = Column(Integer, ForeignKey('procesos_inventario.id'), nullable=False)
    codigo_inventario = Column(String(50), nullable=False)
    codigo_inventario_anterior1 = Column(String(50))
    codigo_inventario_anterior2 = Column(String(50))
    observaciones = Column(String(255))
    fecha_registro = Column(DateTime, nullable=False)
    inventariador_id = Column(Integer, ForeignKey('empleados.id'), nullable=False)
    
    bien = relationship("Bien", back_populates="inventarios")
    proceso_inventario = relationship("ProcesoInventario", back_populates="inventarios_bienes")
    inventariador = relationship("Empleado")

# Agregar relaciones faltantes
Institucion.sedes = relationship("Sede", back_populates="institucion")
Institucion.empleados = relationship("Empleado", back_populates="institucion")
Institucion.bienes = relationship("Bien", back_populates="institucion")
Institucion.procesos_inventario = relationship("ProcesoInventario", back_populates="institucion")
Sede.oficinas = relationship("Oficina", back_populates="sede")
ProcesoInventario.inventarios_bienes = relationship("InventarioBien", back_populates="proceso_inventario")

# Crear las tablas en la base de datos
Base.metadata.create_all(engine)