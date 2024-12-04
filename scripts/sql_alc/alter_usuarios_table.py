import sys
import os
from pathlib import Path

# Añadir la ruta raíz al path de Python
root_path = str(Path(__file__).parent.parent.parent)
sys.path.append(root_path)

from sqlalchemy import create_engine, text
from database import engine

def alter_usuarios_table():
    try:
        with engine.connect() as conn:
            # Agregar nuevas columnas
            print("Agregando nuevas columnas a la tabla usuarios...")
            
            conn.execute(text("""
                ALTER TABLE usuarios 
                ADD COLUMN sede_actual_id INTEGER,
                ADD COLUMN permisos_consulta BOOLEAN DEFAULT FALSE,
                ADD COLUMN permisos_inventario BOOLEAN DEFAULT FALSE;
            """))
            
            # Agregar foreign key para sede_actual_id
            print("Agregando foreign key para sede_actual_id...")
            conn.execute(text("""
                ALTER TABLE usuarios 
                ADD CONSTRAINT fk_sede_actual 
                FOREIGN KEY (sede_actual_id) 
                REFERENCES sedes(id);
            """))
            
            conn.commit()
            print("Tabla usuarios modificada exitosamente")
            
    except Exception as e:
        print(f"Error modificando tabla usuarios: {str(e)}")
        if "Duplicate column name" in str(e):
            print("Una o más columnas ya existen, continuando...")
        else:
            raise e

if __name__ == "__main__":
    print("Iniciando modificación de tabla usuarios...")
    alter_usuarios_table()
    print("Proceso completado")