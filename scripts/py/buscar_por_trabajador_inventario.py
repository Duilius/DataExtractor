from fastapi import HTTPException
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Enum, Boolean, Date, or_, DateTime, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, aliased
from sqlalchemy.sql import select
import enum
from sqlalchemy import cast, String
import os
from datetime import date

# Configuración de la base de datos
DB_URL = f"{os.getenv('DB_TYPE')}://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

class EstadoEmpleado(str, enum.Enum):
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

class NivelJerarquico(enum.Enum):
    NIVEL_1 = 1
    NIVEL_2 = 2
    NIVEL_3 = 3

class Institucion(Base):
    __tablename__ = 'instituciones'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    ruc = Column(String(20), unique=True, nullable=False)
    sedes = relationship("Sede", back_populates="institucion")
    empleados = relationship("Empleado", back_populates="institucion")

class Sede(Base):
    __tablename__ = 'sedes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    institucion_id = Column(Integer, ForeignKey('instituciones.id'), nullable=False)
    nombre = Column(String(100), nullable=False)
    direccion = Column(String(255))
    institucion = relationship("Institucion", back_populates="sedes")
    oficinas = relationship("Oficina", back_populates="sede")

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
    puesto = Column(String(20))
    oficina_id = Column(Integer, ForeignKey('oficinas.id'))
    es_inventariador = Column(Boolean, default=False)
    password_hash = Column(String(255))
    foto_perfil = Column(String(255))
    estado_empleado = Column(Enum(EstadoEmpleado), default=EstadoEmpleado.ACTIVO)
    institucion = relationship("Institucion", back_populates="empleados")
    oficina = relationship("Oficina", back_populates="empleados", foreign_keys=[oficina_id])
    oficina_dirigida = relationship("Oficina", back_populates="jefe", foreign_keys="Oficina.jefe_id")

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
   sede_id = Column(Integer)
   sede =Column(String(50), nullable=True)
   ubicacion_actual =Column(String(300), nullable=True)
   codigo_dni =Column(String(10), nullable=True)
   
   # Relaciones
   empleado_id = Column(Integer, ForeignKey('empleados.id'))
   ubicacion_fisica_id = Column(Integer, ForeignKey('ubicaciones_fisicas.id'), nullable=True)
   
   empleado = relationship("Empleado")

#CONSULTA REGISTRO
def consulta_registro(valor):
    db = Session()
    try:
        # Ajustamos los campos según el modelo actual
        stmt = select(
            Empleado.id,
            Empleado.codigo,
            Empleado.nombre,
            cast(Empleado.estado_empleado, String).label('estado_empleado'),
            Empleado.institucion_id,
            Empleado.puesto,
            Empleado.oficina_id
        ).select_from(Empleado)

        if valor.lower() == "todos":
            pass
        elif valor.isdigit() and len(valor) >= 3:
            stmt = stmt.where(Empleado.codigo.like(f"{valor}%"))
        elif len(valor) >= 3:
            stmt = stmt.where(Empleado.nombre.like(f"{valor}%"))
        else:
            return []

        result = db.execute(stmt)
        return result.all()
    except Exception as e:
        print(f"Error en la consulta: {str(e)}")
        return []
    finally:
        db.close()



#####################CONSULTA AREAS u OFICINAS #########################################
def consulta_area(valor):
    """
    Consulta oficinas por código o nombre según el valor ingresado.
    """
    db = Session()
    try:
        # Base del query para la tabla oficinas
        stmt = select(
            Oficina.id,
            Oficina.codigo,
            Oficina.nombre,
            Oficina.nivel,
            Oficina.sede_id,
            Oficina.institucion_id,
            Oficina.jefe_id
        )

        # Lógica para filtrar la consulta
        if valor.lower() == "todos":
            # No se aplica filtro, devolverá todas las oficinas
            pass
        elif valor.isdigit() and len(valor) >= 3:
            # Si el valor es numérico y tiene al menos 3 dígitos, filtrar por código
            stmt = stmt.where(Oficina.codigo.like(f"{valor}%"))
        elif len(valor) >= 3:
            # Si el valor tiene al menos 3 caracteres, filtrar por nombre
            stmt = stmt.where(Oficina.nombre.like(f"%{valor}%"))
        else:
            # Retornar vacío si no cumple las condiciones mínimas
            return []

        # Ejecutar la consulta
        result = db.execute(stmt).fetchall()

        # Formatear resultados para devolver como JSON
        oficinas = [
            {
                "id": row.id,
                "codigo": row.codigo,
                "nombre": row.nombre,
                "sede_id": row.sede_id,
                "institucion_id": row.institucion_id
            }
            for row in result
        ]

        return oficinas

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la consulta: {str(e)}")
    



#####################CONSULTA AREAS u OFICINAS #########################################
def consulta_codigo(valor, campo):
    """
    Consulta por código: Cod-Patr, Cod-SBN, Cod-2023
    """
    db = Session()
    try:
        # Base del query para la tabla oficinas
        stmt = select(
            AnteriorSis.id,
            AnteriorSis.item,
            AnteriorSis.inv_2023,
            AnteriorSis.codigo_patrimonial,
            AnteriorSis.codigo_nacional,
            AnteriorSis.descripcion,
            AnteriorSis.observaciones,
            AnteriorSis.numero_serie,
            AnteriorSis.inv_2022,
            AnteriorSis.ubicacion_actual,
            AnteriorSis.codigo_dni
        )

        num_dni = AnteriorSis.codigo_dni

        nombres_dni = db.query(Empleado).filter_by(codigo=num_dni).first().nombre

        try:
            if campo == "inv_2023":
                print("que hay ====>", db.query(AnteriorSis).filter_by(inv_2023=valor).first().codigo_dni)
                datos_bien = db.query(AnteriorSis).filter_by(inv_2023=valor).first()
            elif campo == "codigo_nacional":
                datos_bien = db.query(AnteriorSis).filter_by(codigo_nacional=valor).first()
            elif campo == "codigo_patrimonial":
                datos_bien = db.query(AnteriorSis).filter_by(codigo_patrimonial=valor).first()
            elif campo == "inv_2022":
                datos_bien = db.query(AnteriorSis).filter_by(inv_2022=valor).first()
            else:
                return None
        except Exception as e:
            print(f"Error en la búsqueda: {e}")
            return None

        return datos_bien, nombres_dni
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la consulta: {str(e)}")