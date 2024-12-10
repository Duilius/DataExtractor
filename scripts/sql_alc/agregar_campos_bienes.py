from sqlalchemy import create_engine, text
import pandas as pd
import re
import os, claves


engine = create_engine(f"{os.getenv('DB_TYPE')}://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}")


def agregar_campos_bienes():
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                ALTER TABLE bienes
                ADD COLUMN acciones VARCHAR(50),
                ADD COLUMN describe_area VARCHAR(100),
                ADD COLUMN area_actual_id VARCHAR(10),
                ADD CONSTRAINT fk_area_actual 
                FOREIGN KEY (area_actual_id) 
                REFERENCES areas_oficiales(id)
            """))
            conn.commit()
            print("Campos agregados exitosamente")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    agregar_campos_bienes()