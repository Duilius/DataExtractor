
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os, claves

# Configuración de la conexión a la base de datos de Railway
engine = create_engine(f"{os.getenv('DB_TYPE')}://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}")

# Crear sesión
Session = sessionmaker(bind=engine)
session = Session()

# Importar modelos
from create_tables_BD_INVENTARIO import Dependencia, UnidadFuncional, Area, Usuario

def insertar_dependencias():
    dependencias = [
        {"sede_id": 36, "nombre": "JEFATURA DEL SIS"},
        {"sede_id": 36, "nombre": "ORGANO DE CONTROL INSTITUCIONAL"},
        {"sede_id": 36, "nombre": "PROCURADURIA - SIS"},
        {"sede_id": 36, "nombre": "SECRETARIA GENERAL"},
        {"sede_id": 36, "nombre": "OFICINA GENERAL DE ADMINISTRACION DE RECURSOS"},
        {"sede_id": 36, "nombre": "OFICINA GENERAL DE IMAGEN INSTITUCIONAL Y TRANSPARENCIA"},
        {"sede_id": 36, "nombre": "OFICINA GENERAL DE TECNOLOGIA DE LA INFORMACION"},
        {"sede_id": 36, "nombre": "OFICINA GENERAL DE PLANEAMIENTO, PRESUPUESTO Y DESARROLLO ORGANIZACIONAL"},
        {"sede_id": 36, "nombre": "OFICINA GENERAL DE ASESORIA JURIDICA"},
        {"sede_id": 36, "nombre": "GERENCIA DEL ASEGURADO"},
        {"sede_id": 36, "nombre": "GERENCIA DE RIESGOS Y EVALUACION DE LAS PRESTACIONES"},
        {"sede_id": 36, "nombre": "GERENCIA DE NEGOCIOS Y FINANCIAMIENTO"},
        {"sede_id": 36, "nombre": "CAFAE - SIS"}
    ]
    
    # Eliminar registros existentes para esta sede
    session.query(Dependencia).filter_by(sede_id=36).delete()
    
    dependencias_insertadas = []
    
    for dependencia_data in dependencias:
        dependencia = Dependencia(**dependencia_data)
        session.add(dependencia)
        dependencias_insertadas.append(dependencia)
    
    session.commit()
    print("Dependencias insertadas exitosamente.")
    return dependencias_insertadas

def insertar_unidades_funcionales(dependencias):
    # Encontrar la dependencia de Administración de Recursos
    adm_recursos = next(
        (dep for dep in dependencias if dep.nombre == 'OFICINA GENERAL DE ADMINISTRACION DE RECURSOS'), 
        None
    )
    
    if not adm_recursos:
        print("No se encontró la dependencia de Administración de Recursos")
        return []
    
    unidades = [
        {"dependencia_id": adm_recursos.id, "nombre": "UNIDAD FUNCIONAL DE GESTION DE RECURSOS HUMANOS"},
        {"dependencia_id": adm_recursos.id, "nombre": "UNIDAD FUNCIONAL DE ABASTECIMIENTO"},
        {"dependencia_id": adm_recursos.id, "nombre": "UNIDAD FUNCIONAL DE CONTABILIDAD"},
        {"dependencia_id": adm_recursos.id, "nombre": "UNIDAD FUNCIONAL DE TESORERIA"}
    ]
    
    # Eliminar unidades existentes para esta dependencia
    session.query(UnidadFuncional).filter_by(dependencia_id=adm_recursos.id).delete()
    
    unidades_insertadas = []
    
    for unidad_data in unidades:
        unidad = UnidadFuncional(**unidad_data)
        session.add(unidad)
        unidades_insertadas.append(unidad)
    
    session.commit()
    print("Unidades Funcionales insertadas exitosamente.")
    return unidades_insertadas

def insertar_areas(unidades):
    # Encontrar la unidad de Abastecimiento
    abastecimiento = next(uni for uni in unidades if uni['nombre'] == 'UNIDAD FUNCIONAL DE ABASTECIMIENTO')
    
    areas = [
        {"unidad_funcional_id": abastecimiento['id'], "nombre": "CONTROL PATRIMONIAL"},
        {"unidad_funcional_id": abastecimiento['id'], "nombre": "ALMACEN CENTRAL"},
        {"unidad_funcional_id": abastecimiento['id'], "nombre": "SERVICIOS GENERALES"}
    ]
    
    for area_data in areas:
        area = Area(**area_data)
        session.add(area)
    
    session.commit()
    print("Áreas insertadas exitosamente.")

def main():
    try:
        # Insertar en orden
        dependencias = insertar_dependencias()
        unidades = insertar_unidades_funcionales(dependencias)
        insertar_areas(unidades)
        
        print("Todos los datos se han insertado correctamente.")
    
    except Exception as e:
        session.rollback()
        print(f"Error al insertar datos: {e}")
    
    finally:
        session.close()

if __name__ == "__main__":
    main()