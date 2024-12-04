# utils.py
import sys
import os
from pathlib import Path

root_path = str(Path(__file__).parent.parent.parent)
sys.path.append(root_path)
from scripts.sql_alc.auth_models import Usuario
from scripts.py.create_tables_BD_INVENTARIO import Empleado

def obtener_id_usuario(db, codigo: str) -> int:
    """Obtiene ID numérico del empleado por su código."""
    usuario = db.query(Usuario).filter(Usuario.codigo == codigo).first()
    if not usuario:
        raise ValueError(f"Usuario no encontrado: {codigo}")
    return usuario.id


def obtener_id_empleado(db, codigo: str) -> int:
    """Obtiene ID numérico del empleado por su código."""
    empleado = db.query(Empleado).filter(Empleado.codigo == codigo).first()
    if not empleado:
        raise ValueError(f"Empleado no encontrado: {codigo}")
    return empleado.id