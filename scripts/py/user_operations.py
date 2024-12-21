from sqlalchemy.orm import Session
from scripts.sql_alc.create_tables_BD_INVENTARIO import Usuario
from scripts.py.auth_utils import AuthUtils
import os

class UserOperations:
    def __init__(self):
        self.auth_utils = AuthUtils(os.getenv("JWT_SECRET_KEY"))

    def create_user(self, db: Session, user_data: dict):
        """
        Crear usuario con permisos según su rol
        """
        # Validar datos requeridos
        required_fields = ['codigo', 'email', 'tipo_usuario', 'institucion_id']
        for field in required_fields:
            if field not in user_data:
                raise ValueError(f"Campo requerido: {field}")
        
        # Establecer permisos según tipo de usuario
        permisos_consulta = False
        permisos_inventario = False
        
        if user_data['tipo_usuario'] == "Inventariador Proveedor":
            if 'sede_actual_id' not in user_data:
                raise ValueError("Inventariador requiere sede_actual_id")
            permisos_inventario = True
            permisos_consulta = True  # Solo productividad
            
        elif user_data['tipo_usuario'] == "Comisión Cliente":
            permisos_consulta = True
            
        elif user_data['tipo_usuario'] == "Gerencial Proveedor":
            permisos_consulta = True
            permisos_inventario = True
        
        nuevo_usuario = Usuario(
            codigo=user_data['codigo'],
            email=user_data['email'],
            password_hash=self.auth_utils.hash_password(user_data['codigo']),
            tipo_usuario=user_data['tipo_usuario'],
            institucion_id=user_data['institucion_id'],
            sede_actual_id=user_data.get('sede_actual_id'),
            esta_activo=True,
            requiere_cambio_password=True,
            permisos_consulta=permisos_consulta,
            permisos_inventario=permisos_inventario
        )
        
        db.add(nuevo_usuario)
        db.commit()
        db.refresh(nuevo_usuario)
        return nuevo_usuario

    def cambiar_sede_usuario(self, db: Session, usuario_id: int, nueva_sede_id: int):
        """
        Cambiar la sede asignada a un usuario
        """
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        if not usuario:
            raise ValueError("Usuario no encontrado")
            
        if usuario.tipo_usuario not in ["Inventariador Proveedor", "Gerencial Proveedor"]:
            raise ValueError("Usuario no permitido para cambio de sede")
            
        # Registrar el cambio de sede
        usuario.sede_actual_id = nueva_sede_id
        db.commit()
        
        return usuario

# Crear una instancia global para usar en la aplicación
user_operations = UserOperations()