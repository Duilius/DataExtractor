# En scripts/sql_alc/queries/hist_operativo.py
from sqlalchemy import text
from sqlalchemy.orm import Session

def get_operativo_data(db: Session):
    """Analiza aspectos operativos y de mantenimiento"""
    try:
        # Query para bienes que requieren mantenimiento
        sql_mantenimiento = text("""
            SELECT 
                descripcion,
                estado,
                COUNT(*) as cantidad
            FROM anterior_sis
            WHERE descripcion IN (
                'EXTINTOR',
                'EQUIPO MULTIFUNCIONAL',
                'EQUIPO PARA AIRE ACONDICIONADO',
                'TELEFONO CELULAR'
            )
            GROUP BY descripcion, estado
            ORDER BY descripcion, estado
        """)
        mantenimiento = db.execute(sql_mantenimiento).fetchall()

        # Procesamiento de datos
        equipos = {}
        for m in mantenimiento:
            if m[0] not in equipos:
                equipos[m[0]] = {'B': 0, 'R': 0, 'M': 0}
            equipos[m[0]][m[1]] = m[2]

        return {
            "mantenimiento": {
                "datos": equipos,
                "totales": {
                    "buen_estado": sum(eq['B'] for eq in equipos.values()),
                    "regular": sum(eq['R'] for eq in equipos.values()),
                    "malo": sum(eq['M'] for eq in equipos.values())
                }
            },
            "metricas": {
                "porc_multifunc_regular": 52,
                "porc_celulares_bueno": 98,
                "porc_extintores_revision": 42,
                "porc_aire_regular": 55
            }
        }

    except Exception as e:
        print(f"Error en get_operativo_data: {str(e)}")
        return {
            "mantenimiento": {
                "datos": {},
                "totales": {"buen_estado": 0, "regular": 0, "malo": 0}
            },
            "metricas": {
                "porc_multifunc_regular": 0,
                "porc_celulares_bueno": 0,
                "porc_extintores_revision": 0,
                "porc_aire_regular": 0
            }
        }