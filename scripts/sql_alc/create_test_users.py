import sys
import os
from pathlib import Path

root_path = str(Path(__file__).parent.parent.parent)
sys.path.append(root_path)

from database import SessionLocal
from scripts.sql_alc.auth_models import Usuario
from scripts.py.auth_utils import AuthUtils
from scripts.py.create_tables_BD_INVENTARIO import Institucion, Sede
import os

def get_valid_ids():
    db = SessionLocal()
    try:
        instituciones = db.query(Institucion).all()
        sedes = db.query(Sede).all()
        print("\nInstituciones disponibles:")
        for inst in instituciones:
            print(f"ID: {inst.id} - Nombre: {inst.nombre}")
        print("\nSedes disponibles:")
        for sede in sedes:
            print(f"ID: {sede.id} - Nombre: {sede.nombre} (Institución: {sede.institucion_id})")
        return instituciones[0].id if instituciones else None, sedes[0].id if sedes else None
    finally:
        db.close()

def create_test_users():
    # Obtener IDs válidos
    inst_id, sede_id = get_valid_ids()
    if not inst_id or not sede_id:
        print("Error: No hay instituciones o sedes disponibles")
        return

    db = SessionLocal()
    auth_utils = AuthUtils(os.getenv("JWT_SECRET_KEY"))
    
    # Lista de usuarios de prueba
    test_users = [
        {
            "codigo": "INV001",
            "email": "inventariador@empresa.com",
            "password": "INV001",
            "tipo_usuario": "Inventariador Proveedor",
            "institucion_id": inst_id,
            "sede_actual_id": sede_id
        },
        {
            "codigo": "COM001",
            "email": "comision@empresa.com",
            "password": "COM001",
            "tipo_usuario": "Comisión Cliente",
            "institucion_id": inst_id,
            "sede_actual_id": sede_id
        },
        {
            "codigo": "GER001",
            "email": "gerencial@empresa.com",
            "password": "GER001",
            "tipo_usuario": "Gerencial Proveedor",
            "institucion_id": inst_id,
            "sede_actual_id": sede_id
        }
    ]
    
    try:
        for user_data in test_users:
            # Verificar si el usuario ya existe
            existing_user = db.query(Usuario).filter(
                Usuario.codigo == user_data["codigo"]
            ).first()
            
            if existing_user:
                print(f"Usuario {user_data['codigo']} ya existe")
                continue
            
            # Crear nuevo usuario
            new_user = Usuario(
                codigo=user_data["codigo"],
                email=user_data["email"],
                password_hash=auth_utils.hash_password(user_data["password"]),
                tipo_usuario=user_data["tipo_usuario"],
                institucion_id=user_data["institucion_id"],
                sede_actual_id=user_data["sede_actual_id"],
                esta_activo=True,
                requiere_cambio_password=True
            )
            
            db.add(new_user)
            print(f"Usuario {user_data['codigo']} creado exitosamente")
        
        db.commit()
        print("Todos los usuarios fueron creados exitosamente")
        
    except Exception as e:
        print(f"Error creando usuarios: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Creando usuarios de prueba...")
    create_test_users()