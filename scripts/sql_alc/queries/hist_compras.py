from sqlalchemy import func, case, and_, text
from sqlalchemy.orm import Session
from scripts.sql_alc.create_tables_BD_INVENTARIO import Sede, AltasSis2024
from scripts.sql_alc.anterior_sis import AnteriorSis 

def get_compras_data(db: Session):
    """Analiza las compras del 2024"""
    try:
        # Query para distribución por categoría
        sql_distribucion = text("""
            SELECT 
                CASE 
                    WHEN denominacion LIKE '%COMPUTADORA%' OR denominacion LIKE '%SERVIDOR%' OR denominacion LIKE '%RED%' 
                    THEN 'Tecnología'
                    WHEN denominacion LIKE '%SILLA%' OR denominacion LIKE '%ESCRITORIO%' OR denominacion LIKE '%ESTANTE%'
                    THEN 'Mobiliario'
                    WHEN denominacion LIKE '%EQUIPO%'
                    THEN 'Equipos'
                    ELSE 'Otros'
                END as categoria,
                COUNT(*) as cantidad,
                COALESCE(SUM(valor_libros), 0) as valor_total
            FROM altas_sis_2024
            GROUP BY 1
        """)
        distribucion = db.execute(sql_distribucion).fetchall()

        # Query para bienes en desuso
        sql_desuso = text("""
            SELECT 
                COUNT(CASE WHEN situacion != 'D' THEN 1 END) as en_uso,
                COUNT(CASE WHEN situacion = 'D' AND activo_no_depreciable = false THEN 1 END) as sin_uso_dep,
                COUNT(CASE WHEN situacion = 'D' AND activo_no_depreciable = true THEN 1 END) as sin_uso_no_dep,
                COALESCE(SUM(CASE WHEN situacion = 'D' THEN valor_libros ELSE 0 END), 0) as valor_desuso
            FROM altas_sis_2024
        """)
        desuso = db.execute(sql_desuso).fetchone()

        # Query para detalles de bienes en desuso
        sql_detalles = text("""
            SELECT 
                denominacion as categoria,
                COUNT(*) as cantidad,
                COALESCE(SUM(valor_libros), 0) as valor_total,
                (COUNT(*) * 100.0 / (SELECT COUNT(*) FROM altas_sis_2024 WHERE situacion = 'D')) as porcentaje
            FROM altas_sis_2024
            WHERE situacion = 'D'
            GROUP BY denominacion
            ORDER BY COUNT(*) DESC
        """)
        detalles = db.execute(sql_detalles).fetchall()

        # Asegurarnos de que la estructura del diccionario coincida con lo esperado en el template
        return {
            "distribucion": {
                "labels": [d[0] for d in distribucion] if distribucion else [],
                "valores": [float(d[2]) for d in distribucion] if distribucion else [],
                "cantidades": [d[1] for d in distribucion] if distribucion else []
            },
            "desuso": {
                "en_uso": desuso[0] if desuso else 0,
                "sin_uso_depreciables": desuso[1] if desuso else 0,
                "sin_uso_no_depreciables": desuso[2] if desuso else 0,
                "valor_desuso": float(desuso[3]) if desuso else 0
            },
            "detalles_desuso": [
                {
                    "categoria": d[0],
                    "cantidad": d[1],
                    "valor": float(d[2]),
                    "porcentaje": float(d[3])
                }
                for d in detalles
            ] if detalles else [],
            "total_compras": 381,
            "total_valor": 15121130.39
        }

    except Exception as e:
        print(f"Error en get_compras_data: {str(e)}")
        # En caso de error, devolver estructura vacía pero válida
        return {
            "distribucion": {"labels": [], "valores": [], "cantidades": []},
            "desuso": {
                "en_uso": 0,
                "sin_uso_depreciables": 0,
                "sin_uso_no_depreciables": 0,
                "valor_desuso": 0
            },
            "detalles_desuso": [],
            "total_compras": 0,
            "total_valor": 0
        }