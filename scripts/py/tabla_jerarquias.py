from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base, relationship
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

class JerarquiaEmpleados(Base):
    __tablename__ = 'jerarquia_empleados'

    id = Column(Integer, primary_key=True, autoincrement=True)
    jefe_id = Column(Integer, ForeignKey('empleados.id'))
    subordinado_id = Column(Integer, ForeignKey('empleados.id'))
    oficina_id = Column(Integer, ForeignKey('oficinas.id'))
    es_encargatura = Column(Boolean, default=False)
    fecha_inicio = Column(Date)
    fecha_fin = Column(Date)

    jefe = relationship("Empleado", foreign_keys=[jefe_id], back_populates="subordinados")
    subordinado = relationship("Empleado", foreign_keys=[subordinado_id], back_populates="jefes")
    oficina = relationship("Oficina", back_populates="jerarquias")

# Asumiendo que ya tienes definidas las clases Empleado y Oficina
class Empleado(Base):
    __tablename__ = 'empleados'
    id = Column(Integer, primary_key=True)
    # ... otros campos ...
    subordinados = relationship("JerarquiaEmpleados", foreign_keys=[JerarquiaEmpleados.jefe_id], back_populates="jefe")
    jefes = relationship("JerarquiaEmpleados", foreign_keys=[JerarquiaEmpleados.subordinado_id], back_populates="subordinado")

class Oficina(Base):
    __tablename__ = 'oficinas'
    id = Column(Integer, primary_key=True)
    # ... otros campos ...
    jerarquias = relationship("JerarquiaEmpleados", back_populates="oficina")

# Código para crear la tabla en la base de datos
def crear_tablas():
    engine = create_engine(f'{db_type}://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')
    Base.metadata.create_all(engine)

if __name__ == "__main__":
    crear_tablas()