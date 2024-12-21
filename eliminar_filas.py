from sqlalchemy import delete
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from scripts.sql_alc.create_tables_BD_INVENTARIO import Bien  # Reemplaza con el modelo de la tabla original
import os, claves

# Configuración de conexión a la base de datos
engine = create_engine(f"{os.getenv('DB_TYPE')}://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}")

Session = sessionmaker(bind=engine)
session = Session()

# Eliminar filas con código_patrimonial que inicia con 'AF'
query = delete(Bien).where(Bien.codigo_patrimonial.like("AF%"))
session.execute(query)
session.commit()

print("Datos eliminados de 'bienes' con éxito.")
