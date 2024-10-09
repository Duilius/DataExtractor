import random
from datetime import datetime, timedelta
from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models_inventario import Base, Institucion, Sede, Oficina, Empleado, Bien, MovimientoBien, ProcesoInventario, InventarioBien, HistorialEstadoBien, ProcesoBaja, DocumentoOrigenBien, AsignacionBien, SesionConfirmacion, InformeFinalInventario, CacheReporte, EtapaProcesoInventario
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash


import os
import claves

## Variables de conexión a Base de Datos en Railway
db_user=os.getenv("DB_USER")
db_password=os.getenv("DB_PASSWORD")
db_host=os.getenv("DB_HOST")
db_port=os.getenv("DB_PORT")
db_name=os.getenv("DB_NAME")
db_type=os.getenv("DB_TYPE")

# Configuración de la conexión a la base de datos
engine = create_engine(f'{db_type}://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')

#Base = declarative_base()

Session = sessionmaker(bind=engine)
session = Session()

fake = Faker('es_ES')  # Usar el locale español

def create_instituciones(n=5):
    instituciones = []
    for _ in range(n):
        institucion = Institucion(
            nombre=fake.company(),
            ruc=fake.unique.random_number(digits=11, fix_len=True)
        )
        instituciones.append(institucion)
    session.add_all(instituciones)
    session.commit()
    print(f"Creadas {len(instituciones)} instituciones")
    return instituciones

def create_sedes(instituciones, n=10):
    sedes = []
    for _ in range(n):
        sede = Sede(
            institucion=random.choice(instituciones),
            nombre=fake.city(),
            direccion=fake.address()
        )
        sedes.append(sede)
    session.add_all(sedes)
    session.commit()
    print(f"Creadas {len(sedes)} sedes")
    return sedes

def create_oficinas(sedes, n=20):
    oficinas = []
    niveles = ['NIVEL_1', 'NIVEL_2', 'NIVEL_3']
    for _ in range(n):
        oficina = Oficina(
            sede=random.choice(sedes),
            codigo=fake.unique.random_number(digits=5, fix_len=True),
            nombre=fake.job(),
            nivel=random.choice(niveles)
        )
        oficinas.append(oficina)
    session.add_all(oficinas)
    session.commit()
    return oficinas

def create_empleados(instituciones, oficinas, n=50):
    empleados = []
    for _ in range(n):
        empleado = Empleado(
            institucion=random.choice(instituciones),
            codigo=fake.unique.random_number(digits=8, fix_len=True),
            nombre=fake.name(),
            email=fake.email(),
            celular=fake.phone_number(),
            oficina=random.choice(oficinas),
            es_inventariador=fake.boolean(chance_of_getting_true=20),
            foto_perfil=f"perfil_{fake.uuid4()}.jpg"
        )
        empleado.set_password(fake.password())
        empleados.append(empleado)
    session.add_all(empleados)
    session.commit()
    return empleados

def create_bienes(instituciones, n=100):
    bienes = []
    tipos = ['MUEBLE', 'ARTEFACTO']
    estados = ['ACTIVO', 'RAE', 'EN_PROCESO_BAJA', 'DADO_DE_BAJA', 'EN_DONACION']
    for _ in range(n):
        bien = Bien(
            institucion=random.choice(instituciones),
            codigo_patrimonial=fake.unique.random_number(digits=10, fix_len=True),
            descripcion=fake.sentence(),
            tipo=random.choice(tipos),
            material=fake.word(),
            color=fake.color_name(),
            largo=round(random.uniform(0.5, 2.0), 2),
            ancho=round(random.uniform(0.5, 2.0), 2),
            alto=round(random.uniform(0.5, 2.0), 2),
            marca=fake.company() if random.choice(tipos) == 'ARTEFACTO' else None,
            modelo=fake.word() if random.choice(tipos) == 'ARTEFACTO' else None,
            numero_serie=fake.unique.random_number(digits=15, fix_len=True) if random.choice(tipos) == 'ARTEFACTO' else None,
            estado=random.choice(estados),
            imagen_nombre=f"bien_{fake.uuid4()}.jpg"
        )
        bienes.append(bien)
    session.add_all(bienes)
    session.commit()
    return bienes

def create_movimientos_bienes(bienes, empleados, sedes, n=200):
    movimientos = []
    tipos_movimiento = ['ASIGNACION', 'PRESTAMO', 'REPARACION']
    for _ in range(n):
        fecha_desde = fake.date_time_between(start_date='-2y', end_date='now')
        movimiento = MovimientoBien(
            bien=random.choice(bienes),
            empleado_responsable=random.choice(empleados),
            sede_origen=random.choice(sedes),
            sede_destino=random.choice(sedes),
            tipo_movimiento=random.choice(tipos_movimiento),
            fecha_desde=fecha_desde,
            fecha_hasta=fake.date_time_between(start_date=fecha_desde, end_date='now') if random.choice([True, False]) else None
        )
        movimientos.append(movimiento)
    session.add_all(movimientos)
    session.commit()
    return movimientos

def create_procesos_inventario(instituciones, n=10):
    procesos = []
    for _ in range(n):
        year = fake.year()
        proceso = ProcesoInventario(
            institucion=random.choice(instituciones),
            anio=year,
            fecha_inicio=fake.date_between(start_date=f'-{year}-01-01', end_date=f'-{year}-12-31'),
            fecha_fin=fake.date_between(start_date=f'-{year}-01-01', end_date=f'-{year}-12-31'),
            documento_autorizacion=f"AUTH-{fake.uuid4()}",
            fecha_autorizacion=fake.date_between(start_date=f'-{year}-01-01', end_date=f'-{year}-12-31')
        )
        procesos.append(proceso)
    session.add_all(procesos)
    session.commit()
    return procesos

def create_inventarios_bienes(bienes, procesos, empleados, n=500):
    inventarios = []
    for _ in range(n):
        inventario = InventarioBien(
            bien=random.choice(bienes),
            proceso_inventario=random.choice(procesos),
            codigo_inventario=fake.unique.random_number(digits=12, fix_len=True),
            codigo_inventario_anterior1=fake.random_number(digits=12, fix_len=True),
            codigo_inventario_anterior2=fake.random_number(digits=12, fix_len=True),
            observaciones=fake.text(max_nb_chars=200),
            fecha_registro=fake.date_time_between(start_date='-2y', end_date='now'),
            inventariador=random.choice([e for e in empleados if e.es_inventariador]),
            es_faltante=fake.boolean(chance_of_getting_true=5)
        )
        inventarios.append(inventario)
    session.add_all(inventarios)
    session.commit()
    return inventarios

def create_historial_estado_bienes(bienes, n=300):
    historiales = []
    estados = ['ACTIVO', 'RAE', 'EN_PROCESO_BAJA', 'DADO_DE_BAJA', 'EN_DONACION']
    for _ in range(n):
        historial = HistorialEstadoBien(
            bien=random.choice(bienes),
            estado_anterior=random.choice(estados),
            estado_nuevo=random.choice(estados),
            fecha_cambio=fake.date_time_between(start_date='-2y', end_date='now'),
            motivo=fake.sentence()
        )
        historiales.append(historial)
    session.add_all(historiales)
    session.commit()
    return historiales

def create_procesos_baja(bienes, n=50):
    procesos = []
    for _ in range(n):
        proceso = ProcesoBaja(
            bien=random.choice(bienes),
            fecha_inicio=fake.date_between(start_date='-1y', end_date='now'),
            fecha_fin=fake.date_between(start_date='now', end_date='+6m'),
            motivo=fake.sentence(),
            documento_autorizacion=f"BAJA-{fake.uuid4()}"
        )
        procesos.append(proceso)
    session.add_all(procesos)
    session.commit()
    return procesos

def create_documentos_origen_bien(bienes, n=200):
    documentos = []
    tipos_documento = ['Orden de compra', 'Factura', 'Guía de internamiento', 'Donación']
    for _ in range(n):
        documento = DocumentoOrigenBien(
            bien=random.choice(bienes),
            tipo_documento=random.choice(tipos_documento),
            numero_documento=fake.unique.random_number(digits=10, fix_len=True),
            fecha_documento=fake.date_between(start_date='-5y', end_date='now')
        )
        documentos.append(documento)
    session.add_all(documentos)
    session.commit()
    return documentos

def create_asignaciones_bienes(bienes, empleados, procesos, n=300):
    asignaciones = []
    estados = ['Pendiente', 'Confirmado', 'Rechazado']
    for _ in range(n):
        asignacion = AsignacionBien(
            bien=random.choice(bienes),
            empleado=random.choice(empleados),
            proceso_inventario=random.choice(procesos),
            fecha_asignacion=fake.date_time_between(start_date='-1y', end_date='now'),
            estado_confirmacion=random.choice(estados),
            fecha_confirmacion=fake.date_time_between(start_date='-1y', end_date='now') if random.choice([True, False]) else None,
            observaciones=fake.text(max_nb_chars=200)
        )
        asignaciones.append(asignacion)
    session.add_all(asignaciones)
    session.commit()
    return asignaciones

def create_sesiones_confirmacion(empleados, procesos, n=100):
    sesiones = []
    for _ in range(n):
        sesion = SesionConfirmacion(
            empleado=random.choice(empleados),
            proceso_inventario=random.choice(procesos),
            token=fake.uuid4(),
            fecha_creacion=fake.date_time_between(start_date='-1y', end_date='now'),
            fecha_expiracion=fake.date_time_between(start_date='now', end_date='+30d'),
            fecha_confirmacion=fake.date_time_between(start_date='-1y', end_date='now') if random.choice([True, False]) else None,
            ip_confirmacion=fake.ipv4() if random.choice([True, False]) else None,
            mac_address=':'.join(['{:02x}'.format(random.randint(0, 255)) for _ in range(6)]) if random.choice([True, False]) else None
        )
        sesiones.append(sesion)
    session.add_all(sesiones)
    session.commit()
    return sesiones

def create_informes_finales_inventario(procesos, n=10):
    informes = []
    for _ in range(n):
        informe = InformeFinalInventario(
            proceso_inventario=random.choice(procesos),
            fecha_informe=fake.date_between(start_date='-1y', end_date='now'),
            numero_informe=f"INF-{fake.unique.random_number(digits=6, fix_len=True)}",
            resumen_ejecutivo=fake.text(max_nb_chars=500),
            conclusiones=fake.text(max_nb_chars=500),
            recomendaciones=fake.text(max_nb_chars=500)
        )
        informes.append(informe)
    session.add_all(informes)
    session.commit()
    return informes

def create_cache_reportes(n=20):
    caches = []
    for _ in range(n):
        cache = CacheReporte(
            tipo_reporte=fake.word(),
            parametros={"param1": fake.word(), "param2": fake.random_number()},
            resultado={"data": [fake.random_number() for _ in range(5)]},
            fecha_generacion=fake.date_time_between(start_date='-30d', end_date='now'),
            fecha_expiracion=fake.date_time_between(start_date='now', end_date='+30d')
        )
        caches.append(cache)
    session.add_all(caches)
    session.commit()
    return caches

def create_procesos_inventario(instituciones, n=10):
    procesos = []
    for _ in range(n):
        # Generar un año aleatorio entre 2010 y el año actual
        year = fake.random_int(min=2010, max=datetime.now().year)
        
        # Crear objetos date para el inicio y fin del año
        start_of_year = datetime(year, 1, 1)
        end_of_year = datetime(year, 12, 31)
        
        proceso = ProcesoInventario(
            institucion=random.choice(instituciones),
            anio=year,
            fecha_inicio=fake.date_between(start_date=start_of_year, end_date=end_of_year),
            fecha_fin=fake.date_between(start_date=start_of_year, end_date=end_of_year),
            documento_autorizacion=f"AUTH-{fake.uuid4()}",
            fecha_autorizacion=fake.date_between(start_date=start_of_year, end_date=end_of_year)
        )
        procesos.append(proceso)
    session.add_all(procesos)
    session.commit()
    return procesos

def main(clean=False):
    if clean:
        # Limpiar todas las tablas
        session.query(EtapaProcesoInventario).delete()
        session.query(CacheReporte).delete()
        session.query(InformeFinalInventario).delete()
        session.query(SesionConfirmacion).delete()
        session.query(AsignacionBien).delete()
        session.query(DocumentoOrigenBien).delete()
        session.query(ProcesoBaja).delete()
        session.query(HistorialEstadoBien).delete()
        session.query(InventarioBien).delete()
        session.query(MovimientoBien).delete()
        session.query(Bien).delete()
        session.query(Empleado).delete()
        session.query(Oficina).delete()
        session.query(Sede).delete()
        session.query(ProcesoInventario).delete()
        session.query(Institucion).delete()
        session.commit()

    instituciones = create_instituciones(5)
    sedes = create_sedes(instituciones, 10)
    oficinas = create_oficinas(sedes, 20)
    empleados = create_empleados(instituciones, oficinas, 50)
    bienes = create_bienes(instituciones, 100)
    procesos = create_procesos_inventario(instituciones, 10)
    create_movimientos_bienes(bienes, empleados, sedes, 200)
    create_inventarios_bienes(bienes, procesos, empleados, 500)
    create_historial_estado_bienes(bienes, 300)
    create_procesos_baja(bienes, 50)
    create_documentos_origen_bien(bienes, 200)
    create_asignaciones_bienes(bienes, empleados, procesos, 300)
    create_sesiones_confirmacion(empleados, procesos, 100)
    create_informes_finales_inventario(procesos, 10)
    create_cache_reportes(20)
    # Corregido: Pasamos instituciones en lugar de procesos y eliminamos empleados
    create_procesos_inventario(instituciones, 30)

    print("Datos de prueba generados exitosamente.")