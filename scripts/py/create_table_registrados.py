from sqlalchemy import create_engine, Column, Integer, Float, Date, String, DateTime, Time, Boolean
from sqlalchemy.orm import declarative_base
#Es necesario instalar el paquete mysqlclient

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

Base = declarative_base()

class Registrados(Base):
    __tablename__ = 'registrados'
    id_registrado = Column(Integer, primary_key=True,autoincrement=True)
    pais_registrado = Column(String(25))
    ruc_registrado = Column(String(11))
    whatsapp_registrado = Column(String(9))
    nombres_registrado = Column(String(100))
    email_registrado = Column(String(100))
    consulta_registrado = Column(String(255), nullable=True)
    ip_registrado = Column(String(25), nullable=True)
    fec_registrado = Column(Date)
    hora_registrado = Column(Time)
    url_visitada = Column(String(25))
    boton_visitado = Column(String(25))
    dispositivo_conexion = Column(String(25), nullable=True)
    contactado_por = Column(String(25))
    clave_registrado = Column(String(11))
    mensaje_info= Column(String(255))
    mensaje_aprovecha= Column(String(255))
    mensaje_referidos= Column(String(255))
    foto_registrado= Column(String(150))
    fecha_sistema = Column(Date)
    hora_sistema = Column(Time)


Base.metadata.create_all(engine)