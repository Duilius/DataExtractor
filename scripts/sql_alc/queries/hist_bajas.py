from sqlalchemy import func, case, and_, text
from sqlalchemy.orm import Session
from scripts.sql_alc.create_tables_BD_INVENTARIO import Sede, AltasSis2024, BajasSis2024
from scripts.sql_alc.anterior_sis import AnteriorSis 


def get_bajas_data(db: Session):
    """Analiza las bajas del 2024"""
    try:
        # Query para distribución por procedencia
        sql_procedencia = text("""
            SELECT 
                procedencia,
                COUNT(*) as cantidad
            FROM bajas_sis_2024
            GROUP BY procedencia
            ORDER BY COUNT(*) DESC
        """)
        procedencia = db.execute(sql_procedencia).fetchall()

        # Query para estado de bienes
        sql_estado = text("""
            SELECT 
                estado,
                COUNT(*) as cantidad
            FROM bajas_sis_2024
            WHERE procedencia = 'Compras'
            GROUP BY estado
            ORDER BY COUNT(*) DESC
        """)
        estado = db.execute(sql_estado).fetchall()

        # Query para casos especiales - Cambiado 'tipo' por 'denominacion'
        sql_especiales = text("""
            SELECT 
                denominacion,
                estado,
                COUNT(*) as cantidad
            FROM bajas_sis_2024
            WHERE (estado = 'B') OR 
                  (estado = 'R' AND (denominacion LIKE '%AUTO%' OR denominacion LIKE '%CAMIONETA%'))
            GROUP BY denominacion, estado
            ORDER BY estado DESC, COUNT(*) DESC
        """)
        especiales = db.execute(sql_especiales).fetchall()

        return {
            "total_bajas": 971,
            "procedencia": {
                "labels": [p[0] for p in procedencia],
                "cantidades": [p[1] for p in procedencia]
            },
            "estado_bajas": {
                "labels": [e[0] for e in estado],
                "cantidades": [e[1] for e in estado]
            },
            "casos_especiales": [
                {
                    "tipo": e[0],  # mantenemos 'tipo' en el diccionario de retorno
                    "estado": e[1],
                    "cantidad": e[2]
                }
                for e in especiales
            ]
        }

    except Exception as e:
        print(f"Error en get_bajas_data: {str(e)}")
        raise