from sqlalchemy import MetaData, Table
from sqlalchemy import create_engine

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

# Crear una instancia de MetaData
metadata = MetaData()

# Enlazar el motor con la MetaData
metadata.reflect(bind=engine)

# Eliminar la tabla 'tipo_user' de la base de datos
metadata.drop_all(engine, [metadata.tables['registrados']], checkfirst=True)