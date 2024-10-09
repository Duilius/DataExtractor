from sqlalchemy import create_engine, Column, Integer, String, Enum, ForeignKey, MetaData, Table, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
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

# Configuración de la conexión a la base de datos
engine = create_engine(f'{db_type}://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class EstadoEmpleado(enum.Enum):
    ACTIVO = "activo"
    VACACIONES = "vacaciones"
    COMISION_SERVICIO = "comision_servicio"
    CAPACITACION = "capacitacion"
    LICENCIA_MATERNIDAD = "licencia_maternidad"
    LICENCIA_PATERNIDAD = "licencia_paternidad"
    LICENCIA_ENFERMEDAD = "licencia_enfermedad"
    LICENCIA_SIN_GOCE = "licencia_sin_goce"
    LICENCIA_ESTUDIOS = "licencia_estudios"
    SUSPENSION_TEMPORAL = "suspension_temporal"
    SUSPENSION_DISCIPLINARIA = "suspension_disciplinaria"
    JUBILADO = "jubilado"
    CESADO = "cesado"
    RENUNCIA = "renuncia"
    FALLECIDO = "fallecido"
    TRANSFERIDO = "transferido"

class Empleado(Base):
    __tablename__ = 'empleados'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    institucion_id = Column(Integer, ForeignKey('instituciones.id'), nullable=False)
    codigo = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    celular = Column(String(20))
    oficina_id = Column(Integer, ForeignKey('oficinas.id'))
    es_inventariador = Column(String(1), default='0')
    password_hash = Column(String(255))
    foto_perfil = Column(String(255))
    estado_empleado = Column(Enum(EstadoEmpleado), default=EstadoEmpleado.ACTIVO)

def agregar_campo_estado_empleado():
    metadata = MetaData()
    
    # Reflejar la tabla existente
    empleados = Table('empleados', metadata, autoload_with=engine)
    
    # Verificar si la columna ya existe
    if 'estado_empleado' not in empleados.c:
        # Si la columna no existe, añadirla
        try:
            with engine.begin() as connection:
                connection.execute(text("""
                    ALTER TABLE empleados 
                    ADD COLUMN estado_empleado VARCHAR(50) DEFAULT 'activo'
                """))
            print("Campo estado_empleado añadido a la tabla empleados.")
        except OperationalError as e:
            print(f"Error al añadir el campo: {str(e)}")
    else:
        print("El campo estado_empleado ya existe en la tabla empleados.")

if __name__ == "__main__":
    agregar_campo_estado_empleado()