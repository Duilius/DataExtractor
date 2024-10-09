from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import MetaData, Table
from sqlalchemy import create_engine
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

# Configuración de la conexión a la base de datos
# Asegúrate de reemplazar esto con tus propios detalles de conexión
#DATABASE_URL = "mysql://usuario:contraseña@host:puerto/nombre_base_datos"

# Crear el motor de base de datos
#engine = create_engine(DATABASE_URL)

# Crear una sesión
Session = sessionmaker(bind=engine)
session = Session()

# Crear una base declarativa
#Base = declarative_base()

def borrar_tablas_selectivamente(tablas_a_preservar=[]):
    # Obtener el inspector
    inspector = inspect(engine)

    # Obtener nombres de todas las tablas
    tabla_nombres = inspector.get_table_names()

    # Desactivar la verificación de claves foráneas
    session.execute(text("SET FOREIGN_KEY_CHECKS=0"))

    # Borrar cada tabla, excepto las que están en tablas_a_preservar
    for tabla in tabla_nombres:
        if tabla not in tablas_a_preservar:
            session.execute(text(f"DROP TABLE IF EXISTS {tabla}"))
            print(f"Tabla {tabla} eliminada.")
        else:
            print(f"Tabla {tabla} preservada.")

    # Reactivar la verificación de claves foráneas
    session.execute(text("SET FOREIGN_KEY_CHECKS=1"))

    # Commit los cambios
    session.commit()

    print("Proceso de eliminación selectiva completado.")

if __name__ == "__main__":
    # Lista de tablas que quieres preservar
    tablas_a_preservar = ['registrados']
    
    try:
        borrar_tablas_selectivamente(tablas_a_preservar)
    except Exception as e:
        print(f"Ocurrió un error: {e}")
    finally:
        session.close()