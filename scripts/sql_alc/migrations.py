from sqlalchemy import text

import sys
import os
from pathlib import Path

root_path = str(Path(__file__).parent.parent.parent)
sys.path.append(root_path)
from database import SessionLocal

db = SessionLocal()
#upgrade(db)  # Para hacer los cambios
# o 
# downgrade(db)  # Para revertir los cambios si algo sale mal

def upgrade(db):
    try:
        commands = [
            # 1. Agregar columnas en bienes
            """
            ALTER TABLE bienes 
            ADD COLUMN codigo_inventariador VARCHAR(50),
            ADD COLUMN custodio_bien VARCHAR(50)
            """,

            # Agregar constraints para bienes
            """
            ALTER TABLE bienes
            ADD CONSTRAINT fk_codigo_inventariador 
                FOREIGN KEY (codigo_inventariador) REFERENCES usuarios(codigo)
            """,
            """
            ALTER TABLE bienes
            ADD CONSTRAINT fk_custodio_bien 
                FOREIGN KEY (custodio_bien) REFERENCES empleados(codigo)
            """,

            # 2. Agregar columnas en imagenes_bienes
            """
            ALTER TABLE imagenes_bienes 
            ADD COLUMN codigo_inventariador VARCHAR(50),
            ADD COLUMN codigo_custodio VARCHAR(50)
            """,

            # Agregar constraints para imagenes_bienes
            """
            ALTER TABLE imagenes_bienes
            ADD CONSTRAINT fk_img_codigo_inventariador 
                FOREIGN KEY (codigo_inventariador) REFERENCES usuarios(codigo)
            """,
            """
            ALTER TABLE imagenes_bienes
            ADD CONSTRAINT fk_img_codigo_custodio 
                FOREIGN KEY (codigo_custodio) REFERENCES empleados(codigo)
            """,

            # 3. Agregar columnas en asignaciones_bienes
            """
            ALTER TABLE asignaciones_bienes 
            ADD COLUMN fecha_confirmacion TIMESTAMP,
            ADD COLUMN codigo_patrimonial VARCHAR(50),
            ADD COLUMN codigo_inventariador VARCHAR(50)
            """,

            # Agregar constraints para asignaciones_bienes
            """
            ALTER TABLE asignaciones_bienes
            ADD CONSTRAINT fk_asig_codigo_patrimonial 
                FOREIGN KEY (codigo_patrimonial) REFERENCES bienes(codigo_patrimonial)
            """,
            """
            ALTER TABLE asignaciones_bienes
            ADD CONSTRAINT fk_asig_codigo_inventariador 
                FOREIGN KEY (codigo_inventariador) REFERENCES usuarios(codigo)
            """
        ]

        for command in commands:
            try:
                db.execute(text(command))
                db.commit()
                print(f"Comando ejecutado exitosamente: {command[:50]}...")
            except Exception as e:
                print(f"Error en comando {command[:50]}...: {str(e)}")
                continue
        
        print("Migración completada")
        
    except Exception as e:
        db.rollback()
        print(f"Error durante la migración: {str(e)}")
        raise

# Ejecutar la migración
if __name__ == "__main__":
    db = SessionLocal()
    upgrade(db)

