from sqlalchemy import Column, Integer, String, ForeignKey, Float
#from sqlalchemy.orm import relationship 
from base_models import Base

class UbicacionFisica(Base):
   __tablename__ = 'ubicaciones_fisicas'
   id = Column(Integer, primary_key=True, autoincrement=True)
   sede_id = Column(Integer, ForeignKey('sedes.id'), nullable=False)
   oficina_id = Column(Integer, ForeignKey('oficinas.id'), nullable=False) 
   dependencia = Column(String(200), nullable=False)
   ambiente = Column(String(200))
   ubicacion = Column(String(50))

   def __repr__(self):
       return f"<UbicacionFisica(dependencia='{self.dependencia}', ubicacion='{self.ubicacion}')>"