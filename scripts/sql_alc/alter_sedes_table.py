import sys
import os
from pathlib import Path

# Añadir la ruta raíz al path de Python
root_path = str(Path(__file__).parent.parent.parent)
sys.path.append(root_path)

from sqlalchemy import create_engine, text
from database import engine

def alter_sedes_table():
    try:
        with engine.connect() as conn:
            print("Agregando nuevas columnas a la tabla sedes...")
            
            # Agregar nuevas columnas
            conn.execute(text("""
                ALTER TABLE sedes 
                ADD COLUMN cantidad_bienes INTEGER DEFAULT 0,
                ADD COLUMN region VARCHAR(100),
                ADD COLUMN provincia VARCHAR(100),
                ADD COLUMN distrito VARCHAR(100);
            """))
            
            conn.commit()
            print("Tabla sedes modificada exitosamente")
            
    except Exception as e:
        print(f"Error modificando tabla sedes: {str(e)}")
        if "Duplicate column name" in str(e):
            print("Una o más columnas ya existen, continuando...")
        else:
            raise e

if __name__ == "__main__":
    print("Iniciando modificación de tabla sedes...")
    alter_sedes_table()
    print("Proceso completado")