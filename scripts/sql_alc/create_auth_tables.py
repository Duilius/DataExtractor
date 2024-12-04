import sys
import os
from pathlib import Path

# Añadir la ruta raíz al path de Python
root_path = str(Path(__file__).parent.parent.parent)
sys.path.append(root_path)

from database import engine, SessionLocal
from scripts.sql_alc.auth_models import Usuario, TipoUsuario
from scripts.py.auth_utils import AuthUtils
from sqlalchemy import text

def create_table_sql():
    create_table_query = """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INT AUTO_INCREMENT PRIMARY KEY,
        codigo VARCHAR(20) NOT NULL UNIQUE,
        email VARCHAR(100) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        tipo_usuario VARCHAR(50) NOT NULL,
        institucion_id INT,
        sede_id INT,
        empleado_id INT,
        esta_activo BOOLEAN DEFAULT TRUE,
        intentos_fallidos INT DEFAULT 0,
        ultimo_acceso DATETIME,
        fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
        requiere_cambio_password BOOLEAN DEFAULT TRUE,
        FOREIGN KEY (institucion_id) REFERENCES instituciones(id) ON DELETE SET NULL,
        FOREIGN KEY (sede_id) REFERENCES sedes(id) ON DELETE SET NULL,
        FOREIGN KEY (empleado_id) REFERENCES empleados(id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    with engine.connect() as conn:
        try:
            conn.execute(text(create_table_query))
            conn.commit()
            print("Tabla usuarios creada exitosamente")
        except Exception as e:
            print(f"Error al crear la tabla: {str(e)}")

def create_super_admin():
    db = SessionLocal()
    try:
        # Verificar si ya existe un super admin
        existing_admin = db.query(Usuario).filter(
            Usuario.tipo_usuario == TipoUsuario.SUPER_ADMIN.value
        ).first()
        
        if existing_admin:
            print("El Super Admin ya existe.")
            return

        # Crear super admin usando SQL directo
        insert_query = """
        INSERT INTO usuarios (
            codigo, 
            email, 
            password_hash, 
            tipo_usuario, 
            esta_activo, 
            requiere_cambio_password
        ) VALUES (
            :codigo,
            :email,
            :password_hash,
            :tipo_usuario,
            :esta_activo,
            :requiere_cambio_password
        )
        """
        
        # Crear instancia de AuthUtils
        auth_utils = AuthUtils(os.getenv("JWT_SECRET_KEY", "default-secret-key"))
        
        with engine.connect() as conn:
            conn.execute(text(insert_query), {
                "codigo": "ADMIN001",
                "email": "tu@email.com",  # Cambiar por tu email
                "password_hash": auth_utils.hash_password("ADMIN001"),
                "tipo_usuario": TipoUsuario.SUPER_ADMIN.value,
                "esta_activo": True,
                "requiere_cambio_password": True
            })
            conn.commit()
            print("Super Admin creado exitosamente.")
        
    except Exception as e:
        print(f"Error al crear Super Admin: {str(e)}")
        if db:
            db.rollback()

if __name__ == "__main__":
    print("Creando tabla usuarios...")
    create_table_sql()
    
    print("\nCreando Super Admin...")
    create_super_admin()