# Importaciones necesarias
import secrets
from io import BytesIO
from pyzbar.pyzbar import decode
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import io
import base64

import boto3
import traceback
import re
import numpy as np
from openai import OpenAI
from openai import OpenAIError
import json
import os
from typing import List, Dict
from fastapi import FastAPI, Request, HTTPException, Form, UploadFile, File, Depends, Body, APIRouter
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import text, func, case, create_engine, desc
from sqlalchemy import Column, Integer, String, Float, Numeric
from sqlalchemy.orm import sessionmaker
from decimal import Decimal
from datetime import datetime
from utils.dispositivo import determinar_tipo_dispositivo
from database import SessionLocal
from scripts.py.create_tables_BD_INVENTARIO import (Base, Bien, RegistroFallido, MovimientoBien, ImagenBien, HistorialCodigoInventario, AsignacionBien, InventarioBien, TipoBien, TipoMovimiento, ProcesoInventario, Empleado, Oficina)
from scripts.py.buscar_por_trabajador_inventario import consulta_registro

try:
    import claves  # Solo se usará en el entorno local
except ImportError:
    pass


# Configuración de FastAPI, OpenAI, y S3
app = FastAPI()
# Después de crear la app FastAPI y antes de cualquier ruta
from starlette.middleware.sessions import SessionMiddleware
# Después de crear la app FastAPI (app = FastAPI())
app.add_middleware(
    SessionMiddleware,
    secret_key=secrets.token_urlsafe(32),  # Genera una clave secreta aleatoria
    session_cookie="inventario_session"
)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)
client = OpenAI(api_key=os.getenv("inventario_demo_key"))
BUCKET_NAME = "d-ex"
MAX_IMAGE_SIZE = (1024, 1024)

# Configuración de la base de datos
db_url = f"{os.getenv('DB_TYPE')}://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependencia de Base de Datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Funciones utilitarias
def resize_image(image_data: bytes, max_size: tuple = MAX_IMAGE_SIZE) -> bytes:
    with Image.open(BytesIO(image_data)) as img:
        img.thumbnail(max_size)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

def upload_image_to_s3(file_data: bytes, filename: str) -> str:
    try:
        s3_client.put_object(Body=file_data, Bucket=BUCKET_NAME, Key=filename)
        return f"https://{BUCKET_NAME}.s3.amazonaws.com/{filename}"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir la imagen a S3: {str(e)}")

def generate_image_filename(cod_usuario: str, cod_empleado: str, tipo_imagen: str, inv_2024: str) -> str:
    return f"CORPAC-{cod_usuario}-{cod_empleado}-{tipo_imagen}-{inv_2024}.jpg"


# Función para registrar una imagen en la base de datos
def registrar_imagen_en_db(db: Session, bien_id: int, proceso_inventario_id: int, s3_url: str, descripcion: str):
    try:
        if not db:
            print("Error: La sesión de la base de datos (`db`) no está definida.")
            return
        nueva_imagen = ImagenBien(
            bien_id=bien_id,
            url_imagen=s3_url,
            descripcion=descripcion,
            proceso_inventario_id=proceso_inventario_id
        )
        db.add(nueva_imagen)
        db.commit()
        print(f"Imagen registrada en la base de datos con URL: {s3_url}")
    except Exception as e:
        db.rollback()
        print(f"Error al registrar imagen en la base de datos: {str(e)}")


# --------------------------------------------------------------
# Rutas principales para la carga de las diferentes páginas
# --------------------------------------------------------------
@app.get('/')
async def root(request: Request):
    return templates.TemplateResponse("index-mobile.html", {'request': request})

# ------------------------------------------------------------------
# Página de Demostraciones: demos.html , viene de: index-mobile.html
# ------------------------------------------------------------------
@app.get('/pagina-demos')
async def demos(request: Request):
    return templates.TemplateResponse("demos.html", {'request': request}, media_type="text/html")


#######################
# /busca-usuarios
#######################
@app.post('/busca-usuarios')
async def busca_usuarios(request:Request, busca_usuario:str=Form()):
    #print("Se busca a : ====> ", busca_usuario)
    valor = busca_usuario
    users =consulta_registro(valor)
    #print("Resultado =====>", users)

    return templates.TemplateResponse("demo/usuarios_responsables.html",{"request":request,"users":users})


# --------------------------------------------------------------
# Recibe ancho de pantalla (al cargar o al redimensionar)
# --------------------------------------------------------------
@app.post("/cambiar_contenido")
async def cambiar_contenido(request: Request):
    datos = await request.json()
    ancho_pantalla = datos.get("ancho", 0)
    tipo_dispositivo = determinar_tipo_dispositivo(ancho_pantalla)
    
    return templates.TemplateResponse("inventario_activos.html", {'request': request}, media_type="text/html")

# --------------------------------------------------------------
# DNI-EXTRACTOR: Maneja rutas
# --------------------------------------------------------------
@app.get('/dni')
async def dni_root(request: Request):
    return templates.TemplateResponse("dniextractor/ini-dni.html", {'request': request}, media_type="text/html")

@app.post("/contenido_dni")
async def contenido_dni(request: Request):
    datos = await request.json()
    ancho_pantalla = datos.get("ancho", 0)
    tipo_dispositivo = determinar_tipo_dispositivo(ancho_pantalla)
    return templates.TemplateResponse(f"dniextractor/dni-{tipo_dispositivo}.html", {'request': request}, media_type="text/html")

# --------------------------------------------------------------
# FAC-EXTRACTOR: Maneja rutas
# --------------------------------------------------------------
@app.get("/facturas")
async def facturas_root(request: Request):
    return templates.TemplateResponse("facextractor/ini-fac.html", {'request': request}, media_type="text/html")

@app.post("/contenido_fac")
async def contenido_fac(request: Request):
    datos = await request.json()
    ancho_pantalla = datos.get("ancho", 0)
    tipo_dispositivo = determinar_tipo_dispositivo(ancho_pantalla)
    return templates.TemplateResponse(f"facextractor/fac-{tipo_dispositivo}.html", {'request': request}, media_type="text/html")

# --------------------------------------------------------------
# INF-EXTRACTOR: Maneja rutas
# --------------------------------------------------------------
@app.get("/info-extractor")
async def info_extractor_root(request: Request):
    return templates.TemplateResponse("infextractor/ini-inf.html", {'request': request}, media_type="text/html")

@app.post("/contenido_inf")
async def contenido_inf(request: Request):
    datos = await request.json()
    ancho_pantalla = datos.get("ancho", 0)
    tipo_dispositivo = determinar_tipo_dispositivo(ancho_pantalla)
    return templates.TemplateResponse(f"infextractor/inf-{tipo_dispositivo}.html", {'request': request}, media_type="text/html")

# --------------------------------------------------------------
# Recibe "src" del Video de DEMOSTRACIÓN a Cargar
# --------------------------------------------------------------
@app.get("/videos-demo")
async def video_demo(request: Request, origen: str):
    print("Origen del Video", origen)
    return templates.TemplateResponse("videos-demo.html", {'request': request, "origen": origen})

# --------------------------------------------------------------
# Recibe Datos de Registro Nuevo Usuario - Prueba
# --------------------------------------------------------------
@app.post('/newUser/')
async def new_user(request: Request, countryCode: str = Form(), numWa: str = Form(), nombre: str = Form(), consulta: str = Form()):
    print("el nombre es ----------- ", nombre)
    if len(nombre) > 3:
        return RedirectResponse("/servicios")
    else:
        print('muy corto =========== ', nombre)

@app.post('/servicios')
async def servicios(request: Request):
    #return templates.TemplateResponse("demo/inv_demo.html", {'request': request})
    return templates.TemplateResponse("demo/inventario_activos2.html", {'request': request})


@app.get('/demo-inventario')
async def servicios(request: Request):
    return templates.TemplateResponse("demo/inventario_activos2.html", {'request': request})

@app.get('/fotos')
async def fotos(request: Request):
    #return templates.TemplateResponse("demo/inv_demo.html", {'request': request})
    return templates.TemplateResponse("demo/foto_voz.html", {'request': request})

#PROCESA ARCHIVOS HTML (area_search.html y worker_search.html) contenidos en modal (.modal)
#al hacer clic en botones: BUSCAR POR AREA o BUSCAR POR TRABAJADOR
@app.get("/templates/{path:path}", response_class=HTMLResponse)
async def serve_template(request: Request, path: str):
    return templates.TemplateResponse(path, {"request": request})

# --------------------------------------------------------------
# Endpoint de procesamiento de imágenes y extracción con OpenAI
# --------------------------------------------------------------
# Agregar nuevas funciones para manejo de imágenes optimizadas
def optimize_image(image_data: bytes, format: str = 'webp') -> bytes:
    """
    Optimiza la imagen para web: redimensiona y convierte a WebP
    """
    try:
        with Image.open(io.BytesIO(image_data)) as img:
            # Convertir a RGB si es necesario
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.getchannel('A'))
                img = background

            # Redimensionar si excede límites
            if img.size[0] > 1024 or img.size[1] > 1024:
                img.thumbnail((1024, 1024))

            # Optimizar y guardar
            buffer = io.BytesIO()
            if format == 'webp':
                img.save(buffer, format='WebP', quality=80, method=6)
            else:
                img.save(buffer, format='JPEG', quality=85, optimize=True)
            
            return buffer.getvalue()
    except Exception as e:
        print(f"Error optimizando imagen: {str(e)}")
        raise

# Modificar la función determinar_tipo_imagen y agregar procesamiento individual
async def procesar_imagen_individual(base64_image: str) -> dict:
    """
    Procesa una imagen individual con OpenAI para determinar su tipo
    """
    prompt_individual = """
        Analiza esta imagen específica y ÚNICAMENTE extrae:

        Si ves códigos de inventario:
        - Extráelos usando las claves 'INV_2021', 'INV_2023', etc.
        
        Si ves un número de serie:
        - Extráelo usando la clave 'N_Serie'
        
        SOLO si ves el objeto completo (no solo etiquetas o detalles):
        - Describe qué es (usar clave 'descripcion')
        - Indica su color principal (usar clave 'color')
        - Indica su material principal (usar clave 'material')
        
        IMPORTANTE: 
        - NO describas etiquetas o superficies donde están pegadas
        - NO incluyas descripción, color o material si solo ves etiquetas o números de serie
        - Incluye SOLO las claves para los datos que necesitas según las reglas anteriores
        - La respuesta debe ser un JSON válido con comillas dobles
        
        Ejemplo si ves solo etiquetas:
        {
            "INV_2021": "01-11321",
            "INV_2023": "01-21763"
        }

        Ejemplo si ves el objeto completo:
        {
            "descripcion": "Silla de oficina giratoria",
            "color": "azul",
            "material": "tela"
        }
        """

    messages = [
        {"role": "system", "content": "Eres un asistente experto en toma de inventario de bienes."},
        {"role": "user", "content": [
            {"type": "text", "text": prompt_individual},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
        ]}
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=messages,
            max_tokens=150,
            temperature=0
        )
        
        response_text = response.choices[0].message.content.strip()
        print(f"Respuesta de OpenAI: {response_text}")
        
        # Buscar el JSON en la respuesta
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if not json_match:
            print("No se encontró JSON en la respuesta")
            return {}
            
        try:
            datos_imagen = json.loads(json_match.group(0))
            print(f"Datos extraídos de imagen individual: {datos_imagen}")
            return datos_imagen
        except json.JSONDecodeError as e:
            print(f"Error decodificando JSON: {e}")
            print(f"JSON intentado parsear: {json_match.group(0)}")
            return {}
            
    except Exception as e:
        print(f"Error procesando imagen individual: {str(e)}")
        print(f"Respuesta completa: {response.choices[0].message.content if response else 'No response'}")
        return {}

def determinar_tipo_imagen(datos_extraidos: dict) -> str:
    """
    Determina el tipo de imagen basado en los datos extraídos.
    Prioridad: SERIE > PANOR > CODIG
    """
    print(f"Determinando tipo de imagen para datos: {datos_extraidos}")
    
    # Si tiene número de serie, es SERIE
    if 'N_Serie' in datos_extraidos and datos_extraidos['N_Serie'] != "No disponible":
        return 'SERIE'
    
    # Si tiene descripción, es PANOR
    if 'descripcion' in datos_extraidos and datos_extraidos['descripcion'] != "No disponible":
        return 'PANOR'
    
    # Si tiene algún código de inventario, es CODIG
    inv_prefixes = ['INV_', 'codigo_inv_']
    for key in datos_extraidos:
        if any(key.startswith(prefix) for prefix in inv_prefixes):
            if datos_extraidos[key] != "No disponible":
                return 'CODIG'
    
    return 'OTRO'

def generar_nombre_imagen(cod_usuario: str, cod_empleado: str, tipo: str, inv_2024: str, num_imagen: int = None) -> str:
    """
    Genera el nombre final de la imagen según su tipo
    """
    if tipo == 'CODIG' and num_imagen is not None:
        return f"CORPAC-{cod_usuario}-{cod_empleado}-{tipo}-{inv_2024}-{num_imagen}.webp"
    return f"CORPAC-{cod_usuario}-{cod_empleado}-{tipo}-{inv_2024}.webp"

# Inicialización del estado de la aplicación para almacenar imágenes en memoria
app.state.imagenes_procesadas = {}

# Modificar el endpoint upload_fotos existente
@app.post("/upload_fotos")
async def upload_fotos(request: Request, fotos: List[UploadFile] = File(...), uuid: List[str] = Form(...), db: Session = Depends(get_db)):
    session_id = request.session.get('id', 'default')
    
    datos_combinados = {
        "INV_Patrim": "No disponible",
        "INV_2024": "No disponible",
        "INV_2023": "No disponible",
        "INV_2021": "No disponible",
        "INV_2019": "No disponible",
        "Marca": "No disponible",
        "Modelo": "No disponible",
        "N_Serie": "No disponible",
        "descripcion": "No disponible",
        "color": "No disponible",
        "material": "No disponible"
    }

    try:
        imagenes_procesadas = {}
        datos_todas_imagenes = []
        contador_codig = 1  # Contador solo para imágenes tipo CODIG

        # Procesar cada imagen individualmente
        for i, (foto, id_uuid) in enumerate(zip(fotos, uuid)):
            file_content = await foto.read()
            if len(file_content) == 0:
                raise ValueError(f"El archivo {foto.filename} está vacío")

            optimized_image = optimize_image(file_content)
            base64_image = base64.b64encode(optimized_image).decode("utf-8")

            datos_imagen = await procesar_imagen_individual(base64_image)
            tipo = determinar_tipo_imagen(datos_imagen)
            
            # Almacenar información de la imagen
            imagenes_procesadas[id_uuid] = {
                'contenido': optimized_image,
                'tipo': tipo,
                'num_imagen': contador_codig if tipo == 'CODIG' else None
            }
            
            if tipo == 'CODIG':
                contador_codig += 1

            print(f"Imagen {i+1}: UUID={id_uuid}, Tipo={tipo}, Datos={datos_imagen}")
            datos_todas_imagenes.append(datos_imagen)

            # Actualizar datos combinados
            for key, value in datos_imagen.items():
                if key in datos_combinados and value != "No disponible":
                    # Para descripción, color y material, solo tomar de imágenes PANOR
                    if key in ['descripcion', 'color', 'material']:
                        if tipo == 'PANOR':
                            datos_combinados[key] = value
                    # Para otros datos, tomar el primer valor válido encontrado
                    elif datos_combinados[key] == "No disponible":
                        datos_combinados[key] = value

        # Almacenar en el estado de la aplicación
        app.state.imagenes_procesadas[session_id] = imagenes_procesadas
        
        # Almacenar información en la sesión
        request.session['imagenes_info'] = {
            uuid: {
                'tipo': info['tipo'],
                'num_imagen': info['num_imagen']
            } for uuid, info in imagenes_procesadas.items()
        }

        print(f"Procesamiento completado. Tipos de imágenes: {[(uuid, info['tipo']) for uuid, info in imagenes_procesadas.items()]}")
        print(f"Datos combinados finales: {datos_combinados}")
        
        # Convertir claves a mayúsculas para el template
        datos_template = datos_combinados.copy()
        if 'descripcion' in datos_template:
            datos_template['Descripcion'] = datos_template.pop('descripcion')
        if 'color' in datos_template:
            datos_template['Color'] = datos_template.pop('color')
        if 'material' in datos_template:
            datos_template['Material'] = datos_template.pop('material')
        
        return templates.TemplateResponse(
            "demo/datos_inventario_ok.html",
            {"request": request, "datos": datos_template}
        )

    except Exception as e:
        print(f"Error inesperado: {str(e)}")
        traceback.print_exc()
        app.state.imagenes_procesadas.pop(session_id, None)
        return templates.TemplateResponse(
            "demo/datos_inventario_error.html",
            {"request": request, "error": str(e)}
        )

async def upload_to_s3_with_type(image_data: bytes, filename: str) -> str:
    """
    Sube una imagen a S3 y retorna la URL
    """
    try:
        s3_client.put_object(
            Body=image_data,
            Bucket=BUCKET_NAME,
            Key=filename,
            ContentType='image/webp'  # Especificamos el tipo de contenido correcto
        )
        return f"https://{BUCKET_NAME}.s3.amazonaws.com/{filename}"
    except Exception as e:
        print(f"Error al subir a S3: {str(e)}")
        raise

async def process_and_store_images(imagenes: dict, datos: dict, db: Session) -> List[dict]:
    """
    Procesa las imágenes finales, las sube a S3 y registra en la BD
    """
    resultados = []
    contador_codig = 1

    try:
        for uuid, imagen_info in imagenes.items():
            tipo = imagen_info['tipo']
            contenido = imagen_info['contenido']

            # Generar nombre final según tipo
            nombre_final = generar_nombre_imagen(
                cod_usuario=datos['registrador'],
                cod_empleado=datos['worker'],
                tipo=tipo,
                inv_2024=datos['cod_2024'],
                num_imagen=contador_codig if tipo == 'CODIG' else None
            )

            if tipo == 'CODIG':
                contador_codig += 1

            # Subir a S3
            s3_url = await upload_to_s3_with_type(contenido, nombre_final)

            # Registrar en la base de datos
            nueva_imagen = ImagenBien(
                bien_id=datos['bien_id'],  # ID del bien recién registrado
                proceso_inventario_id=datos['proceso_inventario_id'],
                url=s3_url,
                tipo=tipo
            )
            db.add(nueva_imagen)
            
            resultados.append({
                'uuid': uuid,
                'tipo': tipo,
                'url': s3_url
            })

        db.commit()
        return resultados

    except Exception as e:
        db.rollback()
        print(f"Error en process_and_store_images: {str(e)}")
        raise

# Modificar el endpoint registrar_bien existente
@app.post("/registrar_bien")
async def registrar_bien(
    request: Request,
    db: Session = Depends(get_db),
    institucion: str = Form(...),
    worker: str = Form(...),
    registrador: str = Form(...),
    cod_patr: str = Form(None),
    cod_2024: str = Form(...),
    cod_2023: str = Form(None),
    cod_2021: str = Form(None),
    cod_2019: str = Form(None),
    color: str = Form(...),
    material: str = Form(...),
    largo: str = Form(None),
    ancho: str = Form(None),
    alto: str = Form(None),
    marca: str = Form(None),
    modelo: str = Form(None),
    num_serie: str = Form(None),
    descripcion: str = Form(...),
    observaciones: str = Form(None),
    enUso: str = Form(...),
    estado: str = Form(...)
):
    session_id = request.session.get('id', 'default')
    imagenes = app.state.imagenes_procesadas.get(session_id, {})

    if not imagenes:
        return JSONResponse(
            content={"exito": False, "error": "No hay imágenes para procesar"},
            status_code=400
        )

    try:
        # Registro de los datos recibidos para verificación
        datos_recibidos = {
            "institucion": institucion,
            "worker": worker,
            "registrador": registrador,
            "cod_patr": cod_patr,
            "cod_2024": cod_2024,
            "cod_2023": cod_2023,
            "cod_2021": cod_2021,
            "cod_2019": cod_2019,
            "color": color,
            "material": material,
            "largo": largo,
            "ancho": ancho,
            "alto": alto,
            "marca": marca,
            "modelo": modelo,
            "num_serie": num_serie,
            "descripcion": descripcion,
            "observaciones": observaciones,
            "enUso": enUso,
            "estado": estado
        }

        # Verificación de duplicados
        bien_existente_patrim = None
        if cod_patr:
            bien_existente_patrim = db.query(Bien).filter(Bien.codigo_patrimonial == cod_patr).first()
        if bien_existente_patrim:
            raise ValueError("Código patrimonial duplicado")

        bien_existente_2024 = db.query(Bien).filter(Bien.codigo_inv_2024 == cod_2024).first()
        if bien_existente_2024:
            raise ValueError("Código de inventario 2024 duplicado")

        # Registrar el bien
        nuevo_bien = Bien(
            institucion_id=institucion,
            codigo_patrimonial=cod_patr,
            codigo_inv_2024=cod_2024,
            codigo_inv_2023=cod_2023,
            codigo_inv_2021=cod_2021,
            codigo_inv_2019=cod_2019,
            descripcion=descripcion,
            tipo=TipoBien.MUEBLE,
            color=color,
            material=material,
            largo=largo,
            ancho=ancho,
            alto=alto,
            marca=marca,
            modelo=modelo,
            numero_serie=num_serie,
            estado=estado,
            en_uso=(enUso == 'Sí'),
            observaciones=observaciones
        )
        db.add(nuevo_bien)
        db.flush()  # Para obtener el ID del bien

        # Procesar y guardar imágenes
        datos_imagenes = {
            'bien_id': nuevo_bien.id,
            'proceso_inventario_id': int(registrador),  # O el ID que corresponda
            'registrador': registrador,
            'worker': worker,
            'cod_2024': cod_2024
        }

        resultados_imagenes = await process_and_store_images(imagenes, datos_imagenes, db)

        # Registro de asignación
        asignacion = AsignacionBien(
            bien_id=nuevo_bien.id,
            empleado_id=worker,
            proceso_inventario_id=int(registrador),
            fecha_asignacion=func.now(),
            estado_confirmacion="Pendiente"
        )
        db.add(asignacion)
        db.commit()

        # Limpiar imágenes de memoria
        app.state.imagenes_procesadas.pop(session_id, None)

        return JSONResponse(content={
            "exito": True,
            "mensaje": "Bien registrado y asignado correctamente",
            "imagenes": resultados_imagenes
        })

    except ValueError as e:
        db.rollback()
        error_message = str(e)
        print(f"Error de validación: {error_message}")
        
        registro_fallido = RegistroFallido(
            datos_bien=json.dumps(datos_recibidos),
            error=error_message,
            inventariador_id=registrador,
            institucion_id=institucion,
            responsable_id=worker
        )
        db.add(registro_fallido)
        db.commit()

        return JSONResponse(
            content={"exito": False, "error": error_message},
            status_code=400
        )

    except Exception as e:
        db.rollback()
        error_message = "Error al registrar bien en el sistema"
        print(f"Error inesperado: {str(e)}")
        
        registro_fallido = RegistroFallido(
            datos_bien=json.dumps(datos_recibidos),
            error=str(e),
            inventariador_id=registrador,
            institucion_id=institucion,
            responsable_id=worker
        )
        db.add(registro_fallido)
        db.commit()

        return JSONResponse(
            content={"exito": False, "error": error_message},
            status_code=500
        )


# --------------------------------------------------------------
# Endpoint para Enviar Reporte por Email (placeholder)
# --------------------------------------------------------------
@app.post("/enviar_reporte")
async def enviar_reporte():
    # Implementar lógica de generación y envío de reporte
    # Placeholder para futuras implementaciones de reportes
    return JSONResponse(content={"enviado": True})





### CÓDIGO DE BARRAS ------------- CÓDIGO DE BARRAS -------------###

@app.get("/barcode")
async def barcode_page(request: Request):
    return templates.TemplateResponse("barcode.html", {"request": request})

@app.post("/procesar_codigo_barras")
async def procesar_codigo_barras(file: UploadFile = File(...)):
   try:
       contents = await file.read()
       imagen = Image.open(io.BytesIO(contents))
       codigos = decode(imagen)
       
       if not codigos:
           return {"success": False, "mensaje": "No se detectaron códigos de barras"}
           
       draw = ImageDraw.Draw(imagen)
       resultados = []
       
       for codigo in codigos:
           datos = codigo.data.decode("utf-8")
           tipo = codigo.type
           datos_procesados = post_procesar_codigo(tipo, datos)
           
           rect = codigo.rect
           draw.rectangle(
               [rect.left, rect.top, rect.left + rect.width, rect.top + rect.height],
               outline="red",
               width=5
           )
           
           resultados.append({
               "tipo": tipo,
               "datos_originales": datos,
               "datos_procesados": datos_procesados
           })
       
       buffered = io.BytesIO()
       imagen.save(buffered, format="JPEG")
       img_str = base64.b64encode(buffered.getvalue()).decode()
       
       return {
           "success": True,
           "resultados": resultados,
           "imagen_procesada": img_str
       }
       
   except Exception as e:
       print(f"Error en el procesamiento: {str(e)}")
       return JSONResponse(
           content={"success": False, "mensaje": f"Error al procesar la imagen: {str(e)}"},
           status_code=400
       )

def post_procesar_codigo(tipo, datos):
   if tipo == "CODE128" and len(datos) == 7 and datos.startswith("01"):
       return f"{datos[:2]}-{datos[2:]}"
   return datos



## ************************  IBT-GROUP  **************************
@app.get("/ibtgroup")
async def ibtgroup(request: Request):
    return templates.TemplateResponse("demo/ibtgroup.html", {"request": request})





#**************** D A S H B O A R D ******************************
# En ini_dataextractor.py, agregar:

# Definir los modelos de datos
#class Bien(Base):
#    __tablename__ = 'bienes'

#class Oficina(Base):
#    __tablename__ = 'oficinas'

#class Empleado(Base):
#    __tablename__ = 'empleados'

#class RegistroFallido(Base):
#    __tablename__ = 'registros_fallidos'

# Crear la función para obtener la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Crear la API con FastAPI
#app = FastAPI()

router = APIRouter()
@app.get("/dashboard")
async def dashboard_view(request: Request):
    return templates.TemplateResponse("/dashboard/dashboard.html", {
        "request": request
    })


@app.get("/dashboard/kpis")
async def get_dashboard_kpis(db: Session = Depends(get_db)):
    # Obtener año actual para filtrar último inventario
    current_year = datetime.now().year
    
    # 1. Total de bienes activos
    total_bienes = db.query(func.count(Bien.id))\
        .filter(Bien.en_uso == True)\
        .scalar()
    
    # 2. Distribución por estado
    distribucion_estado = db.query(
        Bien.estado,
        func.count(Bien.id).label('cantidad')
    )\
    .filter(Bien.en_uso == True)\
    .group_by(Bien.estado)\
    .all()
    
    # 3. Total por tipo
    distribucion_tipo = db.query(
        Bien.tipo,
        func.count(Bien.id).label('cantidad')
    )\
    .filter(Bien.en_uso == True)\
    .group_by(Bien.tipo)\
    .all()
    
    # 4. Bienes faltantes en último inventario
    faltantes = db.query(func.count(InventarioBien.id))\
        .join(ProcesoInventario)\
        .filter(
            ProcesoInventario.anio == current_year,
            InventarioBien.es_faltante == True
        )\
        .scalar() or 0
    
    # 5. Asignaciones pendientes
    asignaciones_pendientes = db.query(func.count(AsignacionBien.id))\
        .filter(AsignacionBien.estado_confirmacion == 'Pendiente')\
        .scalar()
    
    return {
        "total_bienes": total_bienes,
        "distribucion_estado": [
            {"estado": estado.name, "cantidad": cantidad}
            for estado, cantidad in distribucion_estado
        ],
        "distribucion_tipo": [
            {"tipo": tipo.name, "cantidad": cantidad}
            for tipo, cantidad in distribucion_tipo
        ],
        "faltantes": faltantes,
        "asignaciones_pendientes": asignaciones_pendientes
    }



### IMAGEN DE ÚLTIMO BIEN INVENTARIADO ###   **********  ### IMAGEN DE ÚLTIMO BIEN INVENTARIADO ###

def get_s3_url(key):
    s3 = boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION')
    )
    bucket_name = os.getenv('AWS_S3_BUCKET_NAME')
    return s3.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': key}, ExpiresIn=3600)

@app.get("/dashboard/latest-item")
async def get_latest_inventoried_item(db: Session = Depends(get_db)):
    try:
        # Obtener el último bien inventariado
        latest_item = db.query(Bien).order_by(Bien.id.desc()).first()
        if not latest_item:
            raise HTTPException(status_code=404, detail="No se encontró el último bien inventariado.")

        # Obtener asignación de custodio para el bien
        asignacion = db.query(AsignacionBien).filter(
            AsignacionBien.bien_id == latest_item.id,
            AsignacionBien.estado_confirmacion == "PENDIENTE"
        ).order_by(AsignacionBien.fecha_asignacion.desc()).first()
        
        empleado = db.query(Empleado).filter(
            Empleado.id == asignacion.empleado_id
        ).first() if asignacion else None

        # Obtener la oficina del empleado/custodio
        oficina = db.query(Oficina).filter(
            Oficina.id == empleado.oficina_id
        ).first() if empleado else None

        # Obtener las imágenes del bien, ordenando para que la de tipo "PANOR" sea la primera
        image_priority = ["PANOR", "SERIE", "CODIG"]
        images = db.query(ImagenBien).filter(
            ImagenBien.bien_id == latest_item.id,
            ImagenBien.tipo.in_(image_priority)
        ).order_by(
            case((ImagenBien.tipo == "PANOR", 1), (ImagenBien.tipo == "SERIE", 2), (ImagenBien.tipo == "CODIG", 3))
        ).all()

       # Obtener las imágenes del bien, con URLs presignadas si existen
        image_urls = []
        main_image_url = None
        for img in images:
            if img.url:
                # Extraer solo el nombre del objeto (Key) de la URL completa
                s3_key = img.url.replace('https://d-ex.s3.amazonaws.com/', '')
                
                # Generar la URL presignada con el Key correcto
                presigned_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': BUCKET_NAME,
                        'Key': s3_key
                    },
                    ExpiresIn=3600
                )
                
                image_urls.append({"url": presigned_url, "tipo": img.tipo})
                if img.tipo == "PANOR":
                    main_image_url = presigned_url


        # Formatear la respuesta con los datos necesarios
        result = {
            "main_image": main_image_url or (image_urls[0]["url"] if image_urls else None),
            "images": image_urls,
            "item": {
                "descripcion": latest_item.descripcion,
                "marca": latest_item.marca,
                "modelo": latest_item.modelo,
                "estado": latest_item.estado,
                "codigo_patrimonial": latest_item.codigo_patrimonial,
                "area": oficina.nombre if oficina else "No asignada"
            },
            "custodian": {
                "nombre": empleado.nombre if empleado else None,
                "foto": empleado.foto_perfil if empleado and empleado.foto_perfil else "ruta/a/imagen_default.png"
            }
        }

        return result

    except Exception as e:
        print(f"Error al obtener el último bien inventariado: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener el último bien inventariado.")