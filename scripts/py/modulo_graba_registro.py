from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from scripts.py.create_table_registrados import Registrados
import datetime
from datetime import datetime, timedelta

import os
import claves

## Variables de conexión a Base de Datos en Railway
db_user=os.getenv("DB_USER")
db_password=os.getenv("DB_PASSWORD")
db_host=os.getenv("DB_HOST")
db_port=os.getenv("DB_PORT")
db_name=os.getenv("DB_NAME")
db_type=os.getenv("DB_TYPE")

engine = create_engine(f'{db_type}://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')

Session = sessionmaker(bind=engine)
session = Session()


def graba_registro(datos_formulario):
#countryCode, ruc, numWa, nombre, email, consulta, clave
    print("Los datos ====>", datos_formulario)
    nuevo_registrado=Registrados(**datos_formulario)

    try:
        # Agregar el nuevo registro a la sesión y realizar la inserción en la base de datos
        session.add(nuevo_registrado)
        session.commit()
        # Obtener el ID registrado
        id_registrado = nuevo_registrado.id_registrado
        print(f'El ID registrado es: {id_registrado}')
    except SQLAlchemyError as e:
        # Deshacer los cambios en caso de error
        session.rollback()
        print(f"Error en la inserción: {e}")
    finally:
        # Cerrar la sesión
        session.close()