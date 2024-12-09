from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os, claves
# Conexión a la base de datos
engine = create_engine(f"{os.getenv('DB_TYPE')}://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}")
Session = sessionmaker(bind=engine)
session = Session()

try:
    session.execute(text("""
        INSERT INTO usuarios (codigo, email, password_hash, tipo_usuario, esta_activo, requiere_cambio_password)
        VALUES ('ADMIN', 'admin@test.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/Lewvfuls', 'ADMIN', true, false)
    """))
    session.commit()
    print("Usuario ADMIN creado")
except Exception as e:
    print(f"Error: {e}")
    session.rollback()
finally:
    session.close()