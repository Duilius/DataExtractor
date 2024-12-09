from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from datetime import datetime
import os, claves

# Conexión a la base de datos
engine = create_engine(f"{os.getenv('DB_TYPE')}://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}")
Session = sessionmaker(bind=engine)
session = Session()

# Ejecuta la actualización
try:
   session.execute(text("""
       UPDATE usuarios SET 
       password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/Lewvfuls',
       requiere_cambio_password = false,
       esta_activo = true,
       intentos_fallidos = 0
   """))
   session.commit()
   print("Actualización exitosa")
except Exception as e:
   print(f"Error: {e}")
   session.rollback()
finally:
   session.close()