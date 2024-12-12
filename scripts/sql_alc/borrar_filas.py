from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os,claves
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
engine = create_engine(f"{os.getenv('DB_TYPE')}://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}")
SessionLocal = sessionmaker(bind=engine)

def borrar_registros():
    try:
        session = SessionLocal()
        
        # Borrar en orden para respetar foreign keys
        print("Borrando registros...")
        
        # 1. Borrar imagenes_bienes
        session.execute(text("DELETE FROM imagenes_bienes"))
        print("Registros de imagenes_bienes eliminados")
        
        # 2. Borrar asignaciones_bienes
        session.execute(text("DELETE FROM asignaciones_bienes"))
        print("Registros de asignaciones_bienes eliminados")
        
        # 3. Borrar bienes
        session.execute(text("DELETE FROM bienes"))
        print("Registros de bienes eliminados")
        
        # Commit de los cambios
        session.commit()
        print("Todos los registros han sido eliminados exitosamente")
        
    except Exception as e:
        print(f"Error al borrar registros: {str(e)}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    print("Iniciando proceso de borrado...")
    print(f"Conectando a: {os.getenv('DB_HOST')}")
    borrar_registros()