from sqlalchemy import create_engine, text
import pandas as pd
import re
import os, claves


engine = create_engine(f"{os.getenv('DB_TYPE')}://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}")

def recrear_ubicaciones_fisicas():
   try:
       with engine.connect() as conn:
           # 1. Limpiar referencias y tabla
           print("Limpiando datos...")
           conn.execute(text("UPDATE anterior_sis SET ubicacion_fisica_id = NULL"))
           conn.execute(text("ALTER TABLE anterior_sis DROP FOREIGN KEY anterior_sis_ibfk_2"))
           conn.execute(text("DROP TABLE IF EXISTS historico_ubicaciones"))
           conn.execute(text("DROP TABLE IF EXISTS ubicaciones_fisicas"))
           
           # 2. Recrear tabla
           print("Recreando tabla...")
           conn.execute(text("""
               CREATE TABLE ubicaciones_fisicas (
                   id INT PRIMARY KEY AUTO_INCREMENT,
                   sede_id INT,
                   piso VARCHAR(20),
                   dependencia VARCHAR(200),
                   ambiente VARCHAR(200),
                   tipo_ubicacion VARCHAR(50),
                   fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
                   FOREIGN KEY (sede_id) REFERENCES sedes(id)
               )
           """))
           
           # 3. Insertar datos únicos del CSV
           df = pd.read_csv("SIS-INV-FISICO-2023.csv")
           ubicaciones = df[['DEPENDENCIA', 'AMBIENTE', 'SEDE', 'SEDE_ID']].drop_duplicates().copy()
           ubicaciones['DEPENDENCIA'] = ubicaciones['DEPENDENCIA'].str.strip()
           ubicaciones['AMBIENTE'] = ubicaciones['AMBIENTE'].str.strip()
           
           for _, row in ubicaciones.iterrows():
               piso = None
               if 'PISO' in str(row['SEDE']):
                   piso = row['SEDE'].split('PISO')[1].strip()
               elif any(p in row['AMBIENTE'].upper() for p in ['1ER', '2DO', '3ER', '4TO', '5TO']):
                   piso = row['AMBIENTE'].split()[0] + ' PISO'
               
               conn.execute(text("""
                   INSERT INTO ubicaciones_fisicas 
                   (sede_id, dependencia, ambiente, piso, tipo_ubicacion)
                   VALUES (:sede_id, :dependencia, :ambiente, :piso, 'REGULAR')
               """), {
                   'sede_id': int(row['SEDE_ID']),
                   'dependencia': row['DEPENDENCIA'],
                   'ambiente': row['AMBIENTE'],
                   'piso': piso
               })
           
           # 4. Verificar resultados
           total = conn.execute(text("SELECT COUNT(*) FROM ubicaciones_fisicas")).scalar()
           print(f"Total ubicaciones creadas: {total}")
           
           # 5. Actualizar anterior_sis
           result = conn.execute(text("""
               UPDATE anterior_sis a
               JOIN ubicaciones_fisicas u ON 
                   CAST(a.sede_id AS SIGNED) = u.sede_id AND
                   SUBSTRING_INDEX(SUBSTRING_INDEX(a.ubicacion_actual, ' (', 1), ')', 1) = u.ambiente AND
                   SUBSTRING_INDEX(SUBSTRING_INDEX(a.ubicacion_actual, '(', -1), ')', 1) = u.dependencia
               SET a.ubicacion_fisica_id = u.id
           """))
           
           conn.commit()
           print(f"Registros actualizados en anterior_sis: {result.rowcount}")
           
   except Exception as e:
       print(f"Error: {e}")
       
if __name__ == "__main__":
   recrear_ubicaciones_fisicas()