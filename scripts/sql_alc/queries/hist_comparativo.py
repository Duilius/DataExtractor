# En hist_comparativo.py
from sqlalchemy import text
from sqlalchemy.orm import Session

def get_comparativo_data(db: Session):
    """Obtiene datos comparativos 2022-2023"""
    try:
        # 1. Totales por año
        sql_totales = text("""
            SELECT 
                COUNT(CASE WHEN inv_2022 IS NOT NULL THEN 1 END) as total_2022,
                COUNT(CASE WHEN inv_2023 IS NOT NULL THEN 1 END) as total_2023
            FROM anterior_sis
        """)
        totales = db.execute(sql_totales).fetchone()
        inv_2022 = totales[0]
        inv_2023 = totales[1]
        
        # 2. Estado de bienes 2023
        sql_estado = text("""
            SELECT estado, COUNT(*) as cantidad
            FROM anterior_sis
            WHERE estado IS NOT NULL
            GROUP BY estado
        """)
        estado_2023 = db.execute(sql_estado).fetchall()
        
        # 3. Por sede
        sql_sedes = text("""
            SELECT s.nombre,
                COUNT(CASE WHEN a.inv_2022 IS NOT NULL THEN 1 END) as total_2022,
                COUNT(CASE WHEN a.inv_2023 IS NOT NULL THEN 1 END) as total_2023
            FROM sedes s
            LEFT JOIN anterior_sis a ON s.id = a.sede_id
            WHERE s.nombre != 'Sede Central'
            GROUP BY s.nombre
            HAVING COUNT(a.id) > 0  -- Solo sedes con bienes
            ORDER BY s.nombre
        """)
        por_sede = db.execute(sql_sedes).fetchall()

        return {
            "total_comparison": {
                "labels": ["2022", "2023"],
                "data": [inv_2022, inv_2023]
            },
            "estado_2023": {
                "labels": [estado[0] for estado in estado_2023],
                "data": [estado[1] for estado in estado_2023]
            },
            "por_sede": {
                "labels": [sede[0] for sede in por_sede],
                "data_2022": [sede[1] for sede in por_sede],
                "data_2023": [sede[2] for sede in por_sede]
            }
        }

    except Exception as e:
        print(f"Error en get_comparativo_data: {str(e)}")
        raise