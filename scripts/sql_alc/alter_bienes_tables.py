import sys
import os
from pathlib import Path

root_path = str(Path(__file__).parent.parent.parent)
sys.path.append(root_path)

from sqlalchemy import create_engine, text
from database import engine

def alter_tables():
    try:
        with engine.connect() as conn:
            # Verificar y agregar columna requiere_etiqueta
            conn.execute(text("""
                ALTER TABLE bienes 
                ADD COLUMN requiere_etiqueta BOOLEAN DEFAULT FALSE;
            """))
            print("Columna requiere_etiqueta agregada o ya existe")

            # Verificar y agregar columna tipo_hallazgo
            conn.execute(text("""
                ALTER TABLE bienes 
                ADD COLUMN tipo_hallazgo VARCHAR(50) DEFAULT 'NORMAL';
            """))
            print("Columna tipo_hallazgo agregada o ya existe")

            # Verificar y agregar columna observaciones_hallazgo
            conn.execute(text("""
                ALTER TABLE bienes 
                ADD COLUMN observaciones_hallazgo TEXT;
            """))
            print("Columna observaciones_hallazgo agregada o ya existe")

            # Crear índice
            conn.execute(text("""
                CREATE INDEX idx_tipo_hallazgo 
                ON bienes (tipo_hallazgo);
            """))
            print("Índice creado o ya existe")

            conn.commit()
            print("Tabla bienes modificada exitosamente")
            
    except Exception as e:
        print(f"Error modificando tabla bienes: {str(e)}")
        if "Duplicate column name" in str(e):
            print("La columna ya existe, continuando...")
        elif "Duplicate key name" in str(e):
            print("El índice ya existe, continuando...")
        else:
            raise e

if __name__ == "__main__":
    print("Iniciando modificación de tabla bienes...")
    alter_tables()
    print("Proceso completado")