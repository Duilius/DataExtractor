# services/stats_service.py
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import Depends

class StatsService:
    def __init__(self, db: Session):
        self.db = db

    async def get_sede_stats(self, sede_id: int):
        return self.db.execute("""
            SELECT 
                o.nombre as oficina,
                COUNT(DISTINCT e.id) as cant_empleados,
                COUNT(DISTINCT b.id) as cant_bienes
            FROM oficinas o
            LEFT JOIN empleados e ON e.oficina_id = o.id 
            LEFT JOIN bienes b ON b.empleado_id = e.id
            WHERE o.sede_id = :sede_id
            GROUP BY o.nombre
        """, {"sede_id": sede_id}).fetchall()

    async def get_oficina_detail(self, oficina_id: int):
        return self.db.execute("""
            SELECT 
                e.nombre as empleado,
                COUNT(ia.id) as bienes_anterior,
                COUNT(b.id) as bienes_actual,
                GREATEST(COUNT(ia.id) - COUNT(b.id), 0) as faltantes
            FROM empleados e
            LEFT JOIN inventario_anterior ia ON ia.empleado_id = e.id
            LEFT JOIN bienes b ON b.empleado_id = e.id
            WHERE e.oficina_id = :oficina_id
            GROUP BY e.nombre
        """, {"oficina_id": oficina_id}).fetchall()

    async def get_user_progress(self, user_id: int):
        return self.db.execute("""
            SELECT 
                COUNT(b.id) as procesados,
                COUNT(DISTINCT b.empleado_id) as empleados_visitados
            FROM bienes b
            WHERE b.user_id = :user_id
        """, {"user_id": user_id}).first()