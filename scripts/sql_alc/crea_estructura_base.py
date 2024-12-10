from sqlalchemy import create_engine, text
import pandas as pd
import re
import os, claves


engine = create_engine(f"{os.getenv('DB_TYPE')}://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}")

def crear_estructura_areas():
   try:
       with engine.connect() as conn:
           # 1. Crear tabla areas_oficiales
           conn.execute(text("""
               CREATE TABLE areas_oficiales (
                   id VARCHAR(10) PRIMARY KEY,
                   nombre VARCHAR(200),
                   nivel INTEGER,
                   CONSTRAINT chk_nivel CHECK (nivel IN (1, 2))
               )
           """))
           
           # 2. Insertar áreas principales
           areas = [
               ('01.1', 'JEFATURA DEL SIS', 1),
               ('01.2', 'SECRETARÍA GENERAL', 1),
               ('02.1', 'ÓRGANO DE CONTROL INSTITUCIONAL', 1),
               ('03.1', 'PROCURADURÍA PÚBLICA', 1),
               ('04.1', 'OFICINA GENERAL DE PLANEAMIENTO, PRESUPUESTO Y DESARROLLO ORGANIZACIONAL', 1),
               ('04.2', 'OFICINA GENERAL DE ASESORÍA JURÍDICA', 1),
               ('05.1', 'OFICINA GENERAL DE ADMINISTRACIÓN DE RECURSOS', 1),
               ('05.2', 'OFICINA GENERAL DE IMAGEN INSTITUCIONAL Y TRANSPARENCIA', 1),
               ('05.3', 'OFICINA GENERAL DE TECNOLOGÍA DE LA INFORMACIÓN', 1),
               ('06.1', 'GERENCIA DEL ASEGURADO', 1),
               ('06.2', 'GERENCIA DE RIESGOS Y EVALUACIÓN DE LAS PRESTACIONES', 1),
               ('06.3', 'GERENCIA DE NEGOCIOS Y FINANCIAMIENTO', 1),
               ('07.1', 'GERENCIA MACRO REGIONAL', 1),
               ('07.2', 'FONDO INTANGIBLE SOLIDARIO DE SALUD - FISSAL', 1)
           ]
           
           for area in areas:
               conn.execute(text("""
                   INSERT INTO areas_oficiales (id, nombre, nivel)
                   VALUES (:id, :nombre, :nivel)
               """), {'id': area[0], 'nombre': area[1], 'nivel': area[2]})
           
           # 3. Agregar columna en anterior_sis
           conn.execute(text("""
               ALTER TABLE anterior_sis
               ADD COLUMN area_oficial_id VARCHAR(10),
               ADD CONSTRAINT fk_area_oficial 
               FOREIGN KEY (area_oficial_id) 
               REFERENCES areas_oficiales(id)
           """))
           
           conn.commit()
           print("Estructura creada exitosamente")
           
   except Exception as e:
       print(f"Error: {e}")

if __name__ == "__main__":
   crear_estructura_areas()