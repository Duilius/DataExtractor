from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
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
db = Session()

def consulta_registro(valor):
    #Usuario=Registrados(valor)

    # Verificar si el usuario ha ingresado "todos" (en mayúsculas o minúsculas)
    if valor.lower() == "todos":
        # Retornar todos los registros de usuarios
        return db.query(Registrados.dni_usuario, Registrados.nombres_registrado, Registrados.area_usuario, Registrados.area_jefe_usuario, Registrados.jefe_usuario).all()
        
        # Verificar la cantidad de dígitos o caracteres ingresados por el usuario
    elif valor.isdigit() and len(valor) >= 3:
        # Realizar la búsqueda en el campo dni_usuario que empiece con los primeros 3 dígitos ingresados
        return db.query(Registrados.dni_usuario, Registrados.nombres_registrado, Registrados.area_usuario, Registrados.area_jefe_usuario, Registrados.jefe_usuario).filter(Registrados.dni_usuario.like(f"{valor}%")).all()
    
    elif len(valor) >= 3:
        # Realizar la búsqueda en el campo nombres_registrado que empiece con las primeras 3 letras ingresadas
        return db.query(Registrados.dni_usuario, Registrados.nombres_registrado, Registrados.area_usuario, Registrados.area_jefe_usuario, Registrados.jefe_usuario).filter(Registrados.nombres_registrado.like(f"{valor[:3]}%")).all()

    else:
        # Si no se cumple ninguna condición, retornar una lista vacía
        return []