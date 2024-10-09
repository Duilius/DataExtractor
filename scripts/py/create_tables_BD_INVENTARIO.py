from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Enum, Date, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import text
from werkzeug.security import generate_password_hash, check_password_hash
import enum
from datetime import datetime

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

# Definiciones de enumeraciones
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

class EstadoBien(enum.Enum):
    ACTIVO = "Activo"
    RAE = "RAE"
    EN_PROCESO_BAJA = "En proceso de baja"
    DADO_DE_BAJA = "Dado de baja"
    EN_DONACION = "En donación"

# Definiciones de tablas
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
    jefe = relationship("Empleado", foreign_keys=[jefe_id], back_populates="oficina_dirigida")
    oficina_superior = relationship("Oficina", remote_side=[id], back_populates="oficinas_dependientes")
    oficinas_dependientes = relationship("Oficina", back_populates="oficina_superior")
    empleados = relationship("Empleado", back_populates="oficina", foreign_keys="Empleado.oficina_id")

class Empleado(Base):
    __tablename__ = 'empleados'
    id = Column(Integer, primary_key=True, autoincrement=True)
    institucion_id = Column(Integer, ForeignKey('instituciones.id'), nullable=False)
    codigo = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    celular = Column(String(20))
    oficina_id = Column(Integer, ForeignKey('oficinas.id'))
    es_inventariador = Column(Boolean, default=False)
    password_hash = Column(String(255))
    foto_perfil = Column(String(255))  # Almacena la ruta de la foto

    institucion = relationship("Institucion", back_populates="empleados")
    oficina = relationship("Oficina", back_populates="empleados", foreign_keys=[oficina_id])
    oficina_dirigida = relationship("Oficina", back_populates="jefe", foreign_keys="Oficina.jefe_id")
    bienes_responsable = relationship("MovimientoBien", back_populates="empleado_responsable")
    asignaciones = relationship("AsignacionBien", back_populates="empleado")
    sesiones_confirmacion = relationship("SesionConfirmacion", back_populates="empleado")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
    estado = Column(Enum(EstadoBien), default=EstadoBien.ACTIVO)
    imagen_nombre = Column(String(255))  # Nombre del archivo de imagen
    
    institucion = relationship("Institucion", back_populates="bienes")
    movimientos = relationship("MovimientoBien", back_populates="bien")
    inventarios = relationship("InventarioBien", back_populates="bien")
    asignaciones = relationship("AsignacionBien", back_populates="bien")

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
    documento_autorizacion = Column(String(100))
    fecha_autorizacion = Column(Date)
    
    institucion = relationship("Institucion", back_populates="procesos_inventario")
    etapas = relationship("EtapaProcesoInventario", back_populates="proceso_inventario")
    asignaciones = relationship("AsignacionBien", back_populates="proceso_inventario")
    sesiones_confirmacion = relationship("SesionConfirmacion", back_populates="proceso_inventario")

class EtapaProcesoInventario(Base):
    __tablename__ = 'etapas_proceso_inventario'
    id = Column(Integer, primary_key=True, autoincrement=True)
    proceso_inventario_id = Column(Integer, ForeignKey('procesos_inventario.id'), nullable=False)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    fecha_inicio = Column(Date)
    fecha_fin = Column(Date)
    area_responsable = Column(String(100))
    empleado_responsable_id = Column(Integer, ForeignKey('empleados.id'))
    
    proceso_inventario = relationship("ProcesoInventario", back_populates="etapas")
    empleado_responsable = relationship("Empleado")

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
    es_faltante = Column(Boolean, default=False)
    
    bien = relationship("Bien", back_populates="inventarios")
    proceso_inventario = relationship("ProcesoInventario")
    inventariador = relationship("Empleado")

class HistorialEstadoBien(Base):
    __tablename__ = 'historial_estado_bienes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    bien_id = Column(Integer, ForeignKey('bienes.id'), nullable=False)
    estado_anterior = Column(Enum(EstadoBien))
    estado_nuevo = Column(Enum(EstadoBien), nullable=False)
    fecha_cambio = Column(DateTime, default=datetime.utcnow)
    motivo = Column(String(255))
    
    bien = relationship("Bien")

class ProcesoBaja(Base):
    __tablename__ = 'procesos_baja'
    id = Column(Integer, primary_key=True, autoincrement=True)
    bien_id = Column(Integer, ForeignKey('bienes.id'), nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date)
    motivo = Column(String(100), nullable=False)
    documento_autorizacion = Column(String(100))
    
    bien = relationship("Bien")

class DocumentoOrigenBien(Base):
    __tablename__ = 'documentos_origen_bien'
    id = Column(Integer, primary_key=True, autoincrement=True)
    bien_id = Column(Integer, ForeignKey('bienes.id'), nullable=False)
    tipo_documento = Column(String(50), nullable=False)
    numero_documento = Column(String(50), nullable=False)
    fecha_documento = Column(Date, nullable=False)
    
    bien = relationship("Bien")

class AsignacionBien(Base):
    __tablename__ = 'asignaciones_bienes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    bien_id = Column(Integer, ForeignKey('bienes.id'), nullable=False)
    empleado_id = Column(Integer, ForeignKey('empleados.id'), nullable=False)
    proceso_inventario_id = Column(Integer, ForeignKey('procesos_inventario.id'), nullable=False)
    fecha_asignacion = Column(DateTime, default=datetime.utcnow)
    estado_confirmacion = Column(Enum('Pendiente', 'Confirmado', 'Rechazado'), default='Pendiente')
    fecha_confirmacion = Column(DateTime)
    observaciones = Column(Text)

    bien = relationship("Bien", back_populates="asignaciones")
    empleado = relationship("Empleado", back_populates="asignaciones")
    proceso_inventario = relationship("ProcesoInventario", back_populates="asignaciones")

class SesionConfirmacion(Base):
    __tablename__ = 'sesiones_confirmacion'
    id = Column(Integer, primary_key=True, autoincrement=True)
    empleado_id = Column(Integer, ForeignKey('empleados.id'), nullable=False)
    proceso_inventario_id = Column(Integer, ForeignKey('procesos_inventario.id'), nullable=False)
    token = Column(String(100), unique=True, nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_expiracion = Column(DateTime)
    fecha_confirmacion = Column(DateTime)
    ip_confirmacion = Column(String(50))
    mac_address = Column(String(50))

    empleado = relationship("Empleado", back_populates="sesiones_confirmacion")
    proceso_inventario = relationship("ProcesoInventario", back_populates="sesiones_confirmacion")

class InformeFinalInventario(Base):
    __tablename__ = 'informes_finales_inventario'
    id = Column(Integer, primary_key=True, autoincrement=True)
    proceso_inventario_id = Column(Integer, ForeignKey('procesos_inventario.id'), nullable=False)
    fecha_informe = Column(Date, nullable=False)
    numero_informe = Column(String(50), nullable=False)
    resumen_ejecutivo = Column(Text)
    conclusiones = Column(Text)
    recomendaciones = Column(Text)
    
    proceso_inventario = relationship("ProcesoInventario")

class CacheReporte(Base):
    __tablename__ = 'cache_reportes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    tipo_reporte = Column(String(50), nullable=False)
    parametros = Column(JSON)
    resultado = Column(JSON)
    fecha_generacion = Column(DateTime, default=datetime.utcnow)
    fecha_expiracion = Column(DateTime)


# Crear todas las tablas
Base.metadata.create_all(engine)

print("Tablas creadas exitosamente.")