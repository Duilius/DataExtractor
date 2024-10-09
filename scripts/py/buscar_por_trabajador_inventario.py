from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Enum, Boolean, Date, or_
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
    activo = "activo"
    vacaciones = "vacaciones"
    comision_servicio = "comision_servicio"
    capacitacion = "capacitacion"
    licencia_maternidad = "licencia_maternidad"
    licencia_paternidad = "licencia_paternidad"
    licencia_enfermedad = "licencia_enfermedad"
    licencia_sin_goce = "licencia_sin_goce"
    licencia_estudios = "licencia_estudios"
    suspension_temporal = "suspension_temporal"
    suspension_disciplinaria = "suspension_disciplinaria"
    jubilado = "jubilado"
    cesado = "cesado"
    renuncia = "renuncia"
    fallecido = "fallecido"
    transferido = "transferido"

class Institucion(Base):
    __tablename__ = 'instituciones'
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    oficinas = relationship("Oficina", back_populates="institucion")

class Oficina(Base):
    __tablename__ = 'oficinas'
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    institucion_id = Column(Integer, ForeignKey('instituciones.id'))
    institucion = relationship("Institucion", back_populates="oficinas")
    empleados = relationship("Empleado", back_populates="oficina")

class Empleado(Base):
    __tablename__ = 'empleados'
    id = Column(Integer, primary_key=True)
    codigo = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    celular = Column(String(20))
    oficina_id = Column(Integer, ForeignKey('oficinas.id'))
    es_inventariador = Column(String(1), default='0')
    password_hash = Column(String(255))
    foto_perfil = Column(String(255))
    estado_empleado = Column(Enum(EstadoEmpleado), default=EstadoEmpleado.activo)
    oficina = relationship("Oficina", back_populates="empleados")

class JerarquiaEmpleados(Base):
    __tablename__ = 'jerarquia_empleados'
    id = Column(Integer, primary_key=True)
    jefe_id = Column(Integer, ForeignKey('empleados.id'))
    subordinado_id = Column(Integer, ForeignKey('empleados.id'))
    oficina_id = Column(Integer, ForeignKey('oficinas.id'))
    es_encargatura = Column(Boolean, default=False)
    fecha_inicio = Column(Date)
    fecha_fin = Column(Date)

def consulta_registro(valor):
    db = Session()
    try:
        Jefe = aliased(Empleado, name='jefe')
        OficinaJefe = aliased(Oficina, name='oficina_jefe')

        stmt = select(
            Empleado.id,
            Empleado.codigo,
            Empleado.nombre,
            cast(Empleado.estado_empleado, String).label('estado_empleado'),  # Convertir a String
            Oficina.id.label('oficina_id'),
            Oficina.nombre.label('area_usuario'),
            Jefe.id.label('jefe_id'),
            Jefe.nombre.label('nombre_jefe'),
            OficinaJefe.id.label('oficina_jefe_id'),
            OficinaJefe.nombre.label('area_jefe'),
            JerarquiaEmpleados.es_encargatura
        ).select_from(Empleado)\
         .join(Oficina, Empleado.oficina_id == Oficina.id)\
         .outerjoin(JerarquiaEmpleados, Empleado.id == JerarquiaEmpleados.subordinado_id)\
         .outerjoin(Jefe, JerarquiaEmpleados.jefe_id == Jefe.id)\
         .outerjoin(OficinaJefe, Jefe.oficina_id == OficinaJefe.id)


        if valor.lower() == "todos":
            pass
        elif valor.isdigit() and len(valor) >= 3:
            stmt = stmt.where(Empleado.codigo.like(f"{valor}%"))
        elif len(valor) >= 3:
            stmt = stmt.where(Empleado.nombre.like(f"%{valor}%"))
        else:
            return []

        # Filtramos para obtener la jerarquía actual
        stmt = stmt.where(or_(JerarquiaEmpleados.fecha_fin == None, JerarquiaEmpleados.fecha_fin >= date.today()))

        result = db.execute(stmt)
        return result.all()
    except Exception as e:
        print(f"Error en la consulta: {str(e)}")
        return []
    finally:
        db.close()

# Ejemplo de uso
#if __name__ == "__main__":
#    db = Session()
#    resultados = consulta_registro("Juan", db)
#    for r in resultados:
#        print(f"Código: {r.codigo}, Nombre: {r.nombre}, Área: {r.area_usuario}, "
#              f"Estado: {r.estado_empleado}, Jefe: {r.nombre_jefe}, "
#              f"Área del Jefe: {r.area_jefe}, Es Encargatura: {r.es_encargatura}")
#    db.close()