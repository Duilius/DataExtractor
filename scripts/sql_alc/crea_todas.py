from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
import os, claves

# Configuración de la base de datos
engine = create_engine(f"{os.getenv('DB_TYPE')}://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}")

# Crear Base usando el metadata existente
metadata = MetaData()
Base = declarative_base(metadata=metadata)

# Definir primero el modelo de Sede
class Sede(Base):
    __tablename__ = 'sedes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    institucion_id = Column(Integer, ForeignKey('instituciones.id'), nullable=False)
    nombre = Column(String(100), nullable=False)
    direccion = Column(String(255))
    cantidad_bienes = Column(Integer, default=0)
    region = Column(String(100))
    provincia = Column(String(100))
    distrito = Column(String(100))

# Definir modelos con referencias
class Dependencia(Base):
    __tablename__ = 'dependencias'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sede_id = Column(Integer, ForeignKey('sedes.id'), nullable=False)
    nombre = Column(String(100), nullable=False)

class UnidadFuncional(Base):
    __tablename__ = 'unidades_funcionales'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    dependencia_id = Column(Integer, ForeignKey('dependencias.id'), nullable=False)
    nombre = Column(String(100), nullable=False)

class Area(Base):
    __tablename__ = 'areas'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    unidad_funcional_id = Column(Integer, ForeignKey('unidades_funcionales.id'), nullable=False)
    nombre = Column(String(100), nullable=False)

def crear_tabla(tabla):
    try:
        # Crear la tabla específica
        tabla.__table__.create(bind=engine)
        print(f"Tabla {tabla.__tablename__} creada exitosamente.")
        return True
    except Exception as e:
        print(f"Error al crear la tabla {tabla.__tablename__}: {e}")
        return False

def main():
    # Crear tablas en orden
    crear_tabla(Sede)
    crear_tabla(Dependencia)
    crear_tabla(UnidadFuncional)
    crear_tabla(Area)

if __name__ == "__main__":
    main()