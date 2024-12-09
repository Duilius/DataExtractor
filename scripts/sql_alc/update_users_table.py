# update_users_table.py
from sqlalchemy import create_engine, Column, String, text
import sqlalchemy as sa
from sqlalchemy.engine.url import URL
import sys
import os
from pathlib import Path

root_path = str(Path(__file__).parent.parent.parent)
sys.path.append(root_path)
from database import engine

def column_exists(connection, table_name, column_name):
    result = connection.execute(sa.text(
        f"SHOW COLUMNS FROM {table_name} LIKE '{column_name}'"
    ))
    return result.rowcount > 0

# Configuración de conexión a Railway
def upgrade():
    # Crear conexión a la base de datos
    #url = URL.create(**DB_CONFIG)
    #engine = create_engine(url)

    # Agregar las nuevas columnas
    with engine.connect() as connection:
        # Nuevas columnas principales
        alterations = [
            ("apellidos", "VARCHAR(50) NOT NULL DEFAULT 'Por actualizar'"),
            ("nombres", "VARCHAR(50) NOT NULL DEFAULT 'Por actualizar'"),
            ("celular", "VARCHAR(15) NOT NULL DEFAULT '999999999'"),
            ("reset_password_token", "VARCHAR(100) UNIQUE DEFAULT NULL"),
            ("reset_password_expires", "DATETIME DEFAULT NULL")
        ]

        for column_name, definition in alterations:
            if not column_exists(connection, 'usuarios', column_name):
                connection.execute(sa.text(
                    f"ALTER TABLE usuarios ADD COLUMN {column_name} {definition}"
                ))
                print(f"Columna {column_name} agregada exitosamente")
            else:
                print(f"Columna {column_name} ya existe")

if __name__ == "__main__":
    upgrade()