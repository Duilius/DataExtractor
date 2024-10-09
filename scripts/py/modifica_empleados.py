from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models_inventario import Base, Empleado  # Asegúrate de importar tus modelos correctamente
from werkzeug.security import generate_password_hash

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

def actualizar_empleados():
    session = SessionLocal()
    try:
        empleados = session.query(Empleado).all()
        for empleado in empleados:
            # Actualizar foto_perfil
            empleado.foto_perfil = f"{empleado.codigo}.jpg"
            
            # Actualizar password_hash
            empleado.password_hash = generate_password_hash(empleado.codigo)
            
            # Actualizar email
            nombre, apellido = empleado.nombre.split(' ', 1)
            dominio = empleado.email.split('@')[1]
            empleado.email = f"{nombre[0].lower()}{apellido.lower()}@{dominio}"
        
        session.commit()
        print("Actualización completada con éxito.")
    except Exception as e:
        session.rollback()
        print(f"Error durante la actualización: {str(e)}")
    finally:
        session.close()

if __name__ == "__main__":
    actualizar_empleados()