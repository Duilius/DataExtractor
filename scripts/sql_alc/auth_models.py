from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, func
from sqlalchemy.orm import relationship
from scripts.sql_alc.base_models import Base
from scripts.py.create_tables_BD_INVENTARIO import Institucion, Sede, Empleado
import enum
from datetime import datetime
import sys
import os
from pathlib import Path

# Añadir la ruta raíz al path de Python
root_path = str(Path(__file__).parent.parent.parent)
sys.path.append(root_path)

class TipoUsuario(str, enum.Enum):
    INVENTARIADOR_PROVEEDOR = "Inventariador Proveedor"
    INVENTARIADOR_CLIENTE = "Inventariador Cliente"
    COMISION_CLIENTE = "Comisión Cliente"
    GERENCIAL_PROVEEDOR = "Gerencial Proveedor"
    SUPER_ADMIN = "Super Administrador"

class Usuario(Base):
    __tablename__ = 'usuarios'
    
    id = Column(Integer, primary_key=True)
    codigo = Column(String(20), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    tipo_usuario = Column(String(50), nullable=False)
    apellidos = Column(String(50), nullable=False)
    nombres = Column(String(50), nullable=False)
    celular = Column(String(15), nullable=False)
    institucion_id = Column(Integer, ForeignKey('instituciones.id'), nullable=True)
    sede_actual_id = Column(Integer, ForeignKey('sedes.id'), nullable=True)
    empleado_id = Column(Integer, ForeignKey('empleados.id'), nullable=True)
    esta_activo = Column(Boolean, default=True)
    intentos_fallidos = Column(Integer, default=0)
    ultimo_acceso = Column(DateTime, nullable=True)
    fecha_creacion = Column(DateTime, server_default=func.current_timestamp())
    requiere_cambio_password = Column(Boolean, default=True)
    permisos_consulta = Column(Boolean, default=False)
    permisos_inventario = Column(Boolean, default=False)
    
    # Nuevos campos para recuperación de contraseña
    reset_password_token = Column(String(100), unique=True, nullable=True)
    reset_password_expires = Column(DateTime, nullable=True)
    
    # Relaciones
    institucion = relationship("Institucion", back_populates="usuarios")
    sede_actual = relationship("Sede", back_populates="usuarios_actuales")
    empleado = relationship("Empleado", back_populates="usuario")

    def __repr__(self):
        return f"<Usuario {self.codigo}>"