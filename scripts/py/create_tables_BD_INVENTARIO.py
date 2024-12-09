from sqlalchemy.orm import registry
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Enum, Date, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import declarative_base, relationship, registry
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash
import enum
from datetime import datetime
import os
from scripts.sql_alc.base_models import Base
from database import engine  # Importamos engine desde database.py

try:
    import claves  # Solo se usará en el entorno local
except ImportError:
    pass


# Variables de conexión a Base de Datos en Railway
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")
db_type = os.getenv("DB_TYPE")

#engine = create_engine(f'{db_type}://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')
#Base = declarative_base()

# Crear el registry primero
#mapper_registry = registry()
#Base = mapper_registry.generate_base()

# Enumeraciones
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
    MANTENIMIENTO = "Mantenimiento"
    DEVOLUCION = "Devolución"
    BAJA = "Baja"
    RAE = "RAE"

class EstadoBien(enum.Enum):
    N = "N" #Nuevo
    B = "B" #Bueno
    R = "R" #Regular
    M = "M" #Malo
    X = "X"  # Residuo de Aparatos Eléctricos y Electrónicos
    Y = "Y" #Chatarra

class EstadoAutorizacion(enum.Enum):
    ACTIVO = "Activo"
    EXPIRADO = "Expirado"
    CANCELADO = "Cancelado"

class EstadoEmpleado(enum.Enum):
    ACTIVO = "Activo"
    VACACIONES = "Vacaciones"
    COMISION_SERVICIO = "Comisión de servicio"
    CAPACITACION = "Capacitación"
    LICENCIA_MATERNIDAD = "Licencia de maternidad"
    LICENCIA_PATERNIDAD = "Licencia de paternidad"
    LICENCIA_ENFERMEDAD = "Licencia por enfermedad"
    LICENCIA_SIN_GOCE = "Licencia sin goce"
    LICENCIA_ESTUDIOS = "Licencia por estudios"
    SUSPENSION_TEMPORAL = "Suspensión temporal"
    SUSPENSION_DISCIPLINARIA = "Suspensión disciplinaria"
    JUBILADO = "Jubilado"
    CESADO = "Cesado"
    RENUNCIA = "Renuncia"
    FALLECIDO = "Fallecido"
    TRANSFERIDO = "Transferido"

class EstadoMovimiento(enum.Enum):
    EN_PROCESO = "En proceso"
    COMPLETADO = "Completado"
    CANCELADO = "Cancelado"

class MetodoConfirmacion(enum.Enum):
    CLIC = "Clic"
    IMAGEN = "Imagen"
    VIDEO = "Video"

# Definiciones de Tablas
class CatalogoNacionalBienes(Base):
    __tablename__ = 'catalogo_nacional_bienes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(50), unique=True, nullable=False)
    denominacion = Column(String(255), nullable=False)
    grupo = Column(String(100), nullable=False)
    clase = Column(String(100), nullable=False)
    resolucion = Column(String(100))
    estado = Column(String(50), nullable=False)
    fecha_alta = Column(Date, nullable=False)

class Institucion(Base):
    __tablename__ = 'instituciones'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    ruc = Column(String(20), unique=True, nullable=False)
    sedes = relationship("Sede", back_populates="institucion")
    bienes = relationship("Bien", back_populates="institucion")
    empleados = relationship("Empleado", back_populates="institucion")
    procesos_inventario = relationship("ProcesoInventario", back_populates="institucion")
    usuarios = relationship("Usuario", back_populates="institucion")


class Sede(Base):
    __tablename__ = 'sedes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    institucion_id = Column(Integer, ForeignKey('instituciones.id'), nullable=False)
    nombre = Column(String(100), nullable=False)
    direccion = Column(String(255))
    institucion = relationship("Institucion", back_populates="sedes")
    oficinas = relationship("Oficina", back_populates="sede")
    cantidad_bienes = Column(Integer, default=0)
    region = Column(String(100))
    provincia = Column(String(100))
    distrito = Column(String(100))
    usuarios_actuales = relationship("Usuario", back_populates="sede_actual")

class Oficina(Base):
    __tablename__ = 'oficinas'
    id = Column(Integer, primary_key=True, autoincrement=True)
    sede_id = Column(Integer, ForeignKey('sedes.id'), nullable=False)
    institucion_id = Column(Integer, ForeignKey('instituciones.id'), nullable=False)
    codigo = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    nivel = Column(Enum(NivelJerarquico), nullable=False)
    jefe_id = Column(Integer, ForeignKey('empleados.id'))
    sede = relationship("Sede", back_populates="oficinas")
    institucion = relationship("Institucion")
    jefe = relationship("Empleado", foreign_keys=[jefe_id], back_populates="oficina_dirigida")
    empleados = relationship("Empleado", back_populates="oficina", foreign_keys="Empleado.oficina_id")

class Empleado(Base):
    __tablename__ = 'empleados'
    id = Column(Integer, primary_key=True, autoincrement=True)
    institucion_id = Column(Integer, ForeignKey('instituciones.id'), nullable=False)
    codigo = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    puesto = Column(String(20)) #antes celular
    sede_id = Column(Integer, ForeignKey('sedes.id'), nullable=False)
    oficina_id = Column(Integer, ForeignKey('oficinas.id'))
    es_inventariador = Column(Boolean, default=False)
    password_hash = Column(String(255))
    foto_perfil = Column(String(255))
    estado_empleado = Column(Enum(EstadoEmpleado), default=EstadoEmpleado.ACTIVO)
    institucion = relationship("Institucion", back_populates="empleados")
    oficina = relationship("Oficina", back_populates="empleados", foreign_keys=[oficina_id])
    oficina_dirigida = relationship("Oficina", back_populates="jefe", foreign_keys="Oficina.jefe_id")
    asignaciones = relationship("AsignacionBien", back_populates="empleado")
    usuario = relationship("Usuario", back_populates="empleado")  # Añadir esta línea
    sede = relationship("Sede")
    
class Bien(Base):
    __tablename__ = 'bienes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    institucion_id = Column(Integer, ForeignKey('instituciones.id'), nullable=False)
    sede_actual_id = Column(Integer, ForeignKey('sedes.id'), nullable=True)  # Añadir esta línea
    codigo_patrimonial = Column(String(50), unique=True)
    codigo_nacional = Column(String(50), ForeignKey('catalogo_nacional_bienes.codigo'))
    codigo_inv_2024 = Column(String(50))  # Añadido
    codigo_inv_2023 = Column(String(50))  # Añadido
    codigo_inv_2022 = Column(String(50))  # Añadido
    codigo_inv_2021 = Column(String(50))  # Añadido
    codigo_inv_2020 = Column(String(50))  # Añadido
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
    estado = Column(Enum(EstadoBien), default=EstadoBien.B)
    en_uso = Column(Boolean, default=True)
    num_placa=Column(String(100))
    num_chasis=Column(String(100))
    num_motor=Column(String(100))
    anio_fabricac=Column(Integer)
    observaciones = Column(Text)
    codigo_inventariador = Column(String(50))
    custodio_bien = Column(String(50))
    codigo_oficina = Column(String(50))  # antes era ubicacion

    # Relaciones
    institucion = relationship("Institucion", back_populates="bienes")
    catalogo_nacional = relationship("CatalogoNacionalBienes")
    inventarios = relationship("InventarioBien", back_populates="bien")
    asignaciones = relationship("AsignacionBien", back_populates="bien")
    movimientos = relationship("MovimientoBien", back_populates="bien")
    imagenes = relationship("ImagenBien", back_populates="bien")
    historial_codigos = relationship("HistorialCodigoInventario", back_populates="bien")
    sede_actual = relationship("Sede", foreign_keys=[sede_actual_id])
    

class ImagenBien(Base):
    __tablename__ = 'imagenes_bienes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    bien_id = Column(Integer, ForeignKey('bienes.id'), nullable=False)
    proceso_inventario_id = Column(Integer, ForeignKey('procesos_inventario.id'))  # Nuevo campo
    url = Column(String(255), nullable=False)
    tipo = Column(String(50), nullable=False)  # 'principal', 'secundaria', etc.
    fecha_registro = Column(DateTime, default=func.now())
    codigo_inventariador = Column(String(50))
    codigo_custodio = Column(String(50))
    bien = relationship("Bien", back_populates="imagenes")

class HistorialCodigoInventario(Base):
    __tablename__ = 'historial_codigos_inventario'
    id = Column(Integer, primary_key=True, autoincrement=True)
    bien_id = Column(Integer, ForeignKey('bienes.id'), nullable=False)
    codigo_inventario = Column(String(50), nullable=False)
    anio = Column(Integer, nullable=False)
    fecha_registro = Column(DateTime, default=func.now())
    bien = relationship("Bien", back_populates="historial_codigos")

class AsignacionBien(Base):
    __tablename__ = 'asignaciones_bienes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    bien_id = Column(Integer, ForeignKey('bienes.id'), nullable=False)
    empleado_id = Column(Integer, ForeignKey('empleados.id'), nullable=False)
    proceso_inventario_id = Column(Integer, ForeignKey('procesos_inventario.id'), nullable=False)
    fecha_asignacion = Column(DateTime, default=datetime.utcnow)
    estado_confirmacion = Column(Enum('Pendiente', 'Confirmado', 'Rechazado'), default='Pendiente')
    observaciones = Column(Text)
    fecha_confirmacion = Column(DateTime)
    codigo_patrimonial = Column(String(50))
    codigo_inventariador = Column(String(50))
    bien = relationship("Bien", back_populates="asignaciones")
    empleado = relationship("Empleado", back_populates="asignaciones")
    proceso_inventario = relationship("ProcesoInventario", back_populates="asignaciones")
    confirmaciones = relationship("ConfirmacionAsignacion", back_populates="asignacion")

class ConfirmacionAsignacion(Base):
    __tablename__ = 'confirmaciones_asignacion'
    id = Column(Integer, primary_key=True, autoincrement=True)
    asignacion_id = Column(Integer, ForeignKey('asignaciones_bienes.id'), nullable=False)
    empleado_id = Column(Integer, ForeignKey('empleados.id'), nullable=False)
    fecha_confirmacion = Column(DateTime, default=func.now())
    metodo_confirmacion = Column(Enum(MetodoConfirmacion), nullable=False)
    comentarios = Column(Text)
    imagen_url = Column(String(255))
    video_url = Column(String(255))
    asignacion = relationship("AsignacionBien", back_populates="confirmaciones")
    empleado = relationship("Empleado")

class InventarioBien(Base):
    __tablename__ = 'inventarios_bienes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    bien_id = Column(Integer, ForeignKey('bienes.id'), nullable=False)
    proceso_inventario_id = Column(Integer, ForeignKey('procesos_inventario.id'), nullable=False)
    codigo_inventario = Column(String(50), nullable=False)
    observaciones = Column(Text)
    fecha_registro = Column(DateTime, nullable=False)
    inventariador_id = Column(Integer, ForeignKey('empleados.id'), nullable=False)
    es_faltante = Column(Boolean, default=False)
    bien = relationship("Bien", back_populates="inventarios")
    proceso_inventario = relationship("ProcesoInventario", back_populates="inventarios")
    inventariador = relationship("Empleado")

class EmpresaExterna(Base):
    __tablename__ = 'empresas_externas'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ruc = Column(String(20), unique=True, nullable=False)
    razon_social = Column(String(100), nullable=False)
    direccion = Column(String(255))
    contacto = Column(String(100))
    telefono_contacto = Column(String(50))
    empleados = relationship("EmpleadoExterno", back_populates="empresa")

class EmpleadoExterno(Base):
    __tablename__ = 'empleados_externos'
    id = Column(Integer, primary_key=True, autoincrement=True)
    empresa_externa_id = Column(Integer, ForeignKey('empresas_externas.id'), nullable=False)
    nombre = Column(String(100), nullable=False)
    dni = Column(String(20), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    telefono = Column(String(50))
    foto_perfil = Column(String(255))
    estado_autorizacion = Column(Enum(EstadoAutorizacion), default=EstadoAutorizacion.ACTIVO)
    empresa = relationship("EmpresaExterna", back_populates="empleados")
    autorizaciones = relationship("AutorizacionIngreso", back_populates="empleado")

class AutorizacionIngreso(Base):
    __tablename__ = 'autorizaciones_ingreso'
    id = Column(Integer, primary_key=True, autoincrement=True)
    empleado_externo_id = Column(Integer, ForeignKey('empleados_externos.id'), nullable=False)
    sede_id = Column(Integer, ForeignKey('sedes.id'), nullable=False)
    area_permitida = Column(String(100))
    fecha_inicio = Column(Date)
    fecha_fin = Column(Date)
    estado = Column(Enum(EstadoAutorizacion), nullable=False)
    empleado = relationship("EmpleadoExterno", back_populates="autorizaciones")
    sede = relationship("Sede")

class ProcesoInventario(Base):
    __tablename__ = 'procesos_inventario'
    id = Column(Integer, primary_key=True, autoincrement=True)
    institucion_id = Column(Integer, ForeignKey('instituciones.id'), nullable=False)
    empresa_externa_id = Column(Integer, ForeignKey('empresas_externas.id'))
    anio = Column(Integer, nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date)
    documento_autorizacion = Column(String(100))
    fecha_autorizacion = Column(Date)
    institucion = relationship("Institucion", back_populates="procesos_inventario")
    empresa_externa = relationship("EmpresaExterna")
    asignaciones = relationship("AsignacionBien", back_populates="proceso_inventario")
    inventarios = relationship("InventarioBien", back_populates="proceso_inventario")

class MovimientoBien(Base):
    __tablename__ = 'movimientos_bienes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    bien_id = Column(Integer, ForeignKey('bienes.id'), nullable=False)
    tipo_movimiento = Column(Enum(TipoMovimiento), nullable=False)
    fecha_salida = Column(DateTime, nullable=False)
    fecha_retorno_esperada = Column(DateTime)
    fecha_retorno_real = Column(DateTime)
    destino_tipo = Column(Enum('INTERNO', 'EXTERNO'), nullable=False)
    # Relación con la tabla Bien
    bien = relationship("Bien", back_populates="movimientos")

class RegistroFallido(Base):
    __tablename__ = 'registros_fallidos'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    fecha_hora = Column(DateTime, default=datetime.utcnow)
    datos_bien = Column(Text)
    error = Column(Text)
    inventariador_id = Column(Integer, ForeignKey('empleados.id'))
    institucion_id = Column(Integer, ForeignKey('instituciones.id'))
    sede_id = Column(Integer, ForeignKey('sedes.id'))
    oficina_id = Column(Integer, ForeignKey('oficinas.id'))
    responsable_id = Column(Integer, ForeignKey('empleados.id'))
    jefe_id = Column(Integer, ForeignKey('empleados.id'))

    inventariador = relationship("Empleado", foreign_keys=[inventariador_id])
    institucion = relationship("Institucion")
    sede = relationship("Sede")
    oficina = relationship("Oficina")
    responsable = relationship("Empleado", foreign_keys=[responsable_id])
    jefe = relationship("Empleado", foreign_keys=[jefe_id])

# Al final del archivo, después de definir todas las clases

mapper_registry = registry()

def configure_mappers():
    mapper_registry.configure()

# Crear todas las tablas solo si este archivo se ejecuta directamente
if __name__ == "__main__":
    Base.metadata.create_all(engine)
    print("Tablas creadas exitosamente.")