import sys
import os
from pathlib import Path

root_path = str(Path(__file__).parent.parent.parent)
sys.path.append(root_path)

from sqlalchemy import create_engine, text
from database import engine


def alter_bienes_table():
    try:
        with engine.begin() as conn:
            print("Verificando la existencia de la columna y la clave foránea...")
            
            # Verificar si la columna 'sede_actual_id' ya existe
            result = conn.execute(text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'bienes' AND COLUMN_NAME = 'sede_actual_id';
            """)).fetchone()

            if result:
                print("La columna 'sede_actual_id' ya existe. No se realizará ningún cambio en las columnas.")
            else:
                print("Agregando columna 'sede_actual_id' a la tabla bienes...")
                conn.execute(text("""
                    ALTER TABLE bienes 
                    ADD COLUMN sede_actual_id INTEGER;
                """))

            # Verificar si la clave foránea 'fk_sede_actual' ya existe
            result = conn.execute(text("""
                SELECT CONSTRAINT_NAME 
                FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
                WHERE TABLE_NAME = 'bienes' AND CONSTRAINT_NAME = 'fk_sede_actual';
            """)).fetchone()

            if result:
                print("La clave foránea 'fk_sede_actual' ya existe. No se realizará ningún cambio en las restricciones.")
            else:
                print("Agregando clave foránea 'fk_sede_actual'...")
                conn.execute(text("""
                    ALTER TABLE bienes 
                    ADD COLUMN sede_actual_id INTEGER;
                """))

            print("Modificación de la tabla bienes completada exitosamente.")
            
    except Exception as e:
        print(f"Error modificando tabla bienes: {str(e)}")
        if "Duplicate column name" in str(e):
            print("La columna ya existe, continuando...")
        else:
            raise e

if __name__ == "__main__":
    print("Iniciando modificación de tabla bienes...")
    alter_bienes_table()
    print("Proceso completado")