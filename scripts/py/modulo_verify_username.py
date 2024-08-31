from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi.responses import JSONResponse

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

def busca_username(valor):
    user = db.query(Registrados.id_registrado, Registrados.nombres_registrado).filter(Registrados.email_registrado==valor).first()

    if user:
        response_data = {
            "existe": True,
            "id": user.id_registrado,
            "name": user.nombres_registrado
        }
    else:
        response_data = {
            "existe": False
        }
    
    return response_data
    #return JSONResponse(content=response_data)