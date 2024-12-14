import os, sys
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.orm import sessionmaker
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

from sqlalchemy import inspect

from sqlalchemy import text

"""def modificar_columna_rol():
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE empleados MODIFY COLUMN rol VARCHAR(10)"))
            conn.commit()
            print("Columna rol modificada exitosamente")
    except Exception as e:
        print(f"Error al modificar columna: {e}")"""

def cargar_empleados(csv_path):
    # Primero modificamos la columna
    #modificar_columna_rol()
    
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.lower()
    
    metadata = MetaData()
    empleados = Table('empleados', metadata, autoload_with=engine)
    
    try:
        with engine.connect() as conn:
            for _, row in df.iterrows():
                conn.execute(empleados.insert().values(
                    institucion_id=row['institucion_id'],
                    codigo=str(row['codigo']),
                    nombre=row['nombre'],
                    oficina_id=row['oficina_id'],
                    email=row['email'],
                    es_inventariador=row['es_inventariador'],
                    estado_empleado=row['estado_empleado'],
                    puesto=row['puesto'],
                    rol=row['rol'],
                    sede_id=row['sede_id']
                ))
            conn.commit()
        print("Datos cargados exitosamente")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    cargar_empleados("empleados-sis2.csv")