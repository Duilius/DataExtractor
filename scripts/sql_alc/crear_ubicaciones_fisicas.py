from sqlalchemy import create_engine, text
import pandas as pd
import re
import os, claves


engine = create_engine(f"{os.getenv('DB_TYPE')}://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}")


def insertar_ubicaciones_fisicas():
   try:
       with engine.connect() as conn:
           df = pd.read_csv("SIS-INV-FISICO-2023.csv")
           ubicaciones = df[['DEPENDENCIA', 'AMBIENTE', 'SEDE', 'SEDE_ID']].drop_duplicates()

           # Normalizar strings y extraer pisos
           for _, row in ubicaciones.iterrows():
               piso = None
               ambiente = row['AMBIENTE'].strip()
               
               if 'PISO' in str(row['SEDE']):
                   piso = row['SEDE'].split('PISO')[1].strip()
               elif any(p in ambiente.upper() for p in ['1ER', '2DO', '3ER', '4TO', '5TO']):
                   piso = ambiente.split()[0] + ' PISO'

               tipo = 'REGULAR'
               if 'ALMACEN' in ambiente.upper():
                   tipo = 'ALMACEN'
               elif 'HOSPITAL' in ambiente.upper():
                   tipo = 'EXTERNA'

               try:
                   result = conn.execute(text("""
                       INSERT INTO ubicaciones_fisicas 
                       (sede_id, piso, dependencia, ambiente, tipo_ubicacion)
                       VALUES (:sede_id, :piso, :dependencia, :ambiente, :tipo)
                   """), {
                       'sede_id': row['SEDE_ID'],
                       'piso': piso,
                       'dependencia': row['DEPENDENCIA'].strip(),
                       'ambiente': ambiente,
                       'tipo': tipo
                   })
                   if _ % 100 == 0:
                       conn.commit()
                       print(f"Procesados {_} registros")
               except Exception as e:
                   print(f"Error en registro {_}: {e}")

           conn.commit()
           print("Inserción completada")
           
           # Verificar
           count = conn.execute(text("SELECT COUNT(*) FROM ubicaciones_fisicas")).scalar()
           print(f"Total ubicaciones insertadas: {count}")
           
   except Exception as e:
       print(f"Error general: {e}")

if __name__ == "__main__":
   insertar_ubicaciones_fisicas()