# Importaciones necesarias
import secrets
from io import BytesIO
from pyzbar.pyzbar import decode
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import io
import base64

import boto3
from botocore.config import Config
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
from sqlalchemy import text, func, case, create_engine, desc, or_
from sqlalchemy import Column, Integer, String, Float, Numeric
from sqlalchemy.orm import sessionmaker
from decimal import Decimal
from datetime import datetime
from utils.dispositivo import determinar_tipo_dispositivo
from database import SessionLocal
from scripts.py.create_tables_BD_INVENTARIO import (Base, Bien, RegistroFallido, MovimientoBien, ImagenBien, HistorialCodigoInventario, AsignacionBien, InventarioBien, TipoBien, TipoMovimiento, ProcesoInventario, Empleado, Oficina)
from scripts.py.buscar_por_trabajador_inventario import consulta_registro, consulta_area
import logging
from create_tabla_inventario_anterior import InventarioAnterior

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



print("Current working directory:", os.getcwd())
print("Templates directory exists:", os.path.exists("templates"))
print("Demo template exists:", os.path.exists("templates/demo/areas_ubicadas.html"))


@app.post('/test-htmx')
async def test_htmx(request: Request):
    print("Test endpoint called!")
    return HTMLResponse("<div>HTMX está funcionando!</div>")

@app.get('/htmx-status')
async def htmx_status():
    return {"status": "HTMX endpoint working"}



# Antes del endpoint, agrega esto para verificar
from pathlib import Path
template_path = Path("templates/demo/areas_ubicadas.html")
print("¿Template existe?:", template_path.exists())
print("Ruta absoluta del template:", template_path.absolute())
#########################
# /busca-areas u oficinas
#########################
@app.post('/busca-areas')
async def busca_areas(request: Request):
    try:
        # Primero leemos el body completo
        body = await request.body()
        print("Body recibido:", body)
        
        # Intentamos obtener el form data
        form = await request.form()
        print("Form data:", dict(form))
        
        # Obtenemos ubicacion
        ubicacion = form.get('ubicacion', '')
        print("Ubicación:", ubicacion)
        
        if not ubicacion:
            return JSONResponse({"error": "No se recibió ubicacion"}, status_code=400)
            
        areas = consulta_area(ubicacion)
        print("Áreas encontradas:", areas)
        
        # Agregamos un header para debug
        response = templates.TemplateResponse(
            "demo/areas_ubicadas.html",
            {"request": request, "areas": areas},
            headers={"X-Debug": "Response-Sent"}
        )
        return response
        
    except Exception as e:
        print("Error completo:", str(e))
        import traceback
        print("Traceback:", traceback.format_exc())
        return JSONResponse(
            {"error": str(e), "traceback": traceback.format_exc()},
            status_code=500
        )


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
    return templates.TemplateResponse("demo/inventario_sis.html", {'request': request})


@app.get('/demo-inventario')
async def servicios(request: Request):
    return templates.TemplateResponse("demo/inventario_sis.html", {'request': request})

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
    Analiza esta imagen específica y ÚNICAMENTE extrae los siguientes datos si están presentes:

    - "Codigo_Patrimonial": Códigos que comienzan con "AF".
    - "Codigo_Inventario": Códigos que empiezan con años como "2021", "2022", etc.
    - "Anio_Inventario": Los primeros 4 dígitos de una etiqueta que no comience con "AF".
    - Si ves el objeto completo (no solo etiquetas o detalles):
      - "Descripcion": Una breve descripción del objeto.
      - "Color": El color principal del objeto.
      - "Material": El material principal del objeto.

    IMPORTANTE:
    - NO describas etiquetas o superficies donde están pegadas.
    - NO incluyas descripción, color o material si solo ves etiquetas o números.
    - Incluye SOLO las claves necesarias según las reglas anteriores.
    - La respuesta debe ser un JSON válido con comillas dobles.

    Ejemplo si solo ves etiquetas:
    {
        "Codigo_Patrimonial": "AF12345",
        "Codigo_Inventario": "2023-00123",
        "Anio_Inventario": "2023"
    }

    Ejemplo si ves el objeto completo:
    {
        "Descripcion": "Computadora portátil",
        "Color": "negro",
        "Material": "plástico"
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


def buscar_en_inventario(db: Session, codigos: List[str]) -> Dict[str, str]:
    resultados = {}
    codigos = list(set(codigos))  # Elimina duplicados antes de buscar

    for codigo in codigos:
        # Verificar si ya se buscó este código previamente
        if codigo in resultados:
            continue  # Saltar al siguiente código para evitar duplicados

        # Caso 1: Código patrimonial
        if codigo.startswith("AF"):
            result = db.query(InventarioAnterior).filter_by(codigo_patrimonial=codigo).first()
            resultados[codigo] = result if result else "faltante"

            if result:
                print(f"Resultado para {codigo}: id={result.id}, descripcion={result.descripcion}, marca={result.marca}")
            else:
                print(f"No se encontró resultado para {codigo}")

        # Caso 2: Código de inventario
        elif codigo.startswith("2023") or codigo.startswith("2022"):
            result = db.query(InventarioAnterior).filter(
                or_(
                    InventarioAnterior.codigo_inv_2023 == codigo,
                    InventarioAnterior.codigo_inv_2022 == codigo
                )
            ).first()
            resultados[codigo] = result if result else "faltante"

            if result:
                print(f"Resultado para {codigo}: id={result.id}, descripcion={result.descripcion}, marca={result.marca}")
            else:
                print(f"No se encontró resultado para {codigo}")
    
    return resultados


def determinar_mensaje(codigos: List[str], resultados: Dict[str, str]) -> str:
    if not codigos:
        return "POSIBLE NUEVO"
    if any(codigo.startswith("AF") and resultados.get(codigo) == "faltante" for codigo in codigos):
        return "POSIBLE SOBRANTE"
    if any(
        (codigo.startswith("2023") or codigo.startswith("2022"))
        and not any(c.startswith("AF") for c in codigos)
        and resultados.get(codigo) == "faltante"
        for codigo in codigos
    ):
        return "POSIBLE SOBRANTE"
    if any(
        (codigo.startswith("2023") or codigo.startswith("2022"))
        and not any(c.startswith("AF") for c in codigos)
        and resultados.get(codigo) == "existe"
        for codigo in codigos
    ):
        return "SIN COD PATR"
    return "N/A"


def actualizar_situacion_sis(db: Session, codigos: List[str]) -> str:
    if any(codigo.startswith("AF") for codigo in codigos):
        return "BIEN FALTANTE"
    if any(
        codigo.startswith("2023") or codigo.startswith("2022") for codigo in codigos
    ):
        return "ETIQUETAR COD PATR"
    return "N/A"

def obtener_valores_inventario(resultado):
    # Asignar el código patrimonial
    codigo_patr = resultado.codigo_patrimonial if resultado.codigo_patrimonial else None
    
    # Asignar los códigos de inventario correspondientes, verificando si existen en los campos de la tabla
    codigos_inventario = {
        "cod-patr": codigo_patr,
        "cod-2023": resultado.codigo_inv_2023 if resultado.codigo_inv_2023 else None,
        "cod-2022": resultado.codigo_inv_2022 if resultado.codigo_inv_2022 else None,
        "cod-2021": resultado.codigo_inv_2021 if resultado.codigo_inv_2021 else None,
        "cod-2020": resultado.codigo_inv_2020 if resultado.codigo_inv_2020 else None
    }

    return codigos_inventario

# Modificar el endpoint upload_fotos existente
@app.post("/upload_fotos")
async def upload_fotos(
    request: Request,
    fotos: List[UploadFile] = File(...),
    uuid: List[str] = Form(...),
    db: Session = Depends(get_db)
):
    session_id = request.session.get('id', 'default')
    resultados_busqueda = []

    try:
        for foto in fotos:
            # Leer y procesar la imagen
            file_content = await foto.read()
            if len(file_content) == 0:
                raise ValueError(f"El archivo {foto.filename} está vacío")

            optimized_image = optimize_image(file_content)
            base64_image = base64.b64encode(optimized_image).decode("utf-8")

            # Extraer datos de la imagen
            datos_imagen = await procesar_imagen_individual(base64_image)

            codigo_patrimonial = datos_imagen.get("Codigo_Patrimonial")
            codigo_inventario = datos_imagen.get("Codigo_Inventario")

            # Consultar en la base de datos utilizando buscar_en_inventario
            if codigo_patrimonial or codigo_inventario:
                codigos = [codigo_patrimonial, codigo_inventario]
                resultados = buscar_en_inventario(db, codigos)

                # Filtrar resultados válidos
                for codigo, resultado in resultados.items():
                    if isinstance(resultado, InventarioAnterior):
                        resultados_busqueda.append(resultado)
                    else:
                        print(f"No se encontró resultado para {codigo}")

                # Generar los valores para el diccionario
                for dato in resultados_busqueda:
                    codigos_inventario = obtener_valores_inventario(dato)

                    # Verificar los valores que se asignan
                    print(f"Resultado para {dato.codigo_patrimonial}: {codigos_inventario}")

        # Preparar los datos para pasar a la plantilla
        datos_para_plantilla = [
            {
                "mensaje": codigos_inventario.get("mensaje", "Mensaje no disponible"),
                "situacion_sis": codigos_inventario.get("situacion_sis", "Situación no especificada"),
                "codigo_patr": dato.codigo_patrimonial if dato.codigo_patrimonial else "Sin código patrimonial",
                "codigo_inv_2023": dato.codigo_inv_2023 if dato.codigo_inv_2023 else "No disponible",
                "codigo_inv_2022": dato.codigo_inv_2022 if dato.codigo_inv_2022 else "No disponible",
                "codigo_inv_2021": dato.codigo_inv_2021 if dato.codigo_inv_2021 else "No disponible",
                "codigo_inv_2020": dato.codigo_inv_2020 if dato.codigo_inv_2020 else "No disponible",
                "descripcion": dato.descripcion if dato.descripcion else "Sin descripción",
                "material": dato.material if dato.material else "Material no disponible",
                "color": dato.color if dato.color else "Color no disponible",
                "marca": dato.marca if dato.marca else "Marca no disponible",
                "modelo": dato.modelo if dato.modelo else "Modelo no disponible",
                "largo": dato.largo if dato.largo else "Largo no disponible",
                "ancho": dato.ancho if dato.ancho else "Ancho no disponible",
                "alto": dato.alto if dato.alto else "Alto no disponible",
                "numero_serie": dato.numero_serie if dato.numero_serie else "N° Serie no disponible",
                "observaciones": dato.observaciones if dato.observaciones else "Observaciones no disponible",
                "anio_fabricac": dato.anio_fabricac if dato.anio_fabricac else "Año no disponible",
                "estado": dato.estado if dato.estado else "Estado no disponible",
                "num_placa": dato.num_placa if dato.num_placa else "Placa no disponible",
                "num_chasis": dato.num_chasis if dato.num_chasis else "N° Chasis no disponible",
                "num_motor": dato.num_motor if dato.num_motor else "N° Serie motor no disponible"
            }
            for dato in resultados_busqueda
        ]

        print(f"Datos enviados a la plantilla: {datos_para_plantilla}")

        datos_para_plantilla = [datos_para_plantilla[:1]]
        return templates.TemplateResponse(
            "demo/datos_inventario_ok.html",
            {"request": request, "datos": datos_para_plantilla}
        )

    except Exception as e:
        print(f"Error inesperado: {e}")
        traceback.print_exc()
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


def validar_dimensiones(valor: str) -> float:
    """
    Valida que el valor recibido sea numérico y lo convierte a float.
    Si el valor es None, vacío o no numérico, retorna 0.
    """
    try:
        return float(valor)
    except (TypeError, ValueError):
        
        return 0.0


# Modificar el endpoint registrar_bien existente
@app.post("/registrar_bien")
async def registrar_bien(
    request: Request,
    db: Session = Depends(get_db),
    institucion: str = Form(...),
    worker: str = Form(...),
    ubicacion: str = Form(...),  # Nuevo campo
    registrador: str = Form(...),
    cod_patr: str = Form(None),
    cod_2024: str = Form(...),
    cod_2023: str = Form(None),
    cod_2022: str = Form(None),
    cod_2021: str = Form(None),
    cod_2020: str = Form(None),
    color: str = Form(...),
    material: str = Form(...),
    largo: str = Form(None),
    ancho: str = Form(None),
    alto: str = Form(None),
    marca: str = Form(None),
    modelo: str = Form(None),
    num_serie: str = Form(None),
    situacion_sis: str = Form(...),  # Nuevo campo
    situacion_prov: str = Form(...),  # Nuevo campo
    num_placa: str = Form(None),  # Nuevo campo
    num_chasis: str = Form(None),  # Nuevo campo
    num_motor: str = Form(None),  # Nuevo campo
    anio_fabricac: str = Form(None),  # Nuevo campo
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
        # Validar y convertir las dimensiones
        largo_validado = validar_dimensiones(largo)
        ancho_validado = validar_dimensiones(ancho)
        alto_validado = validar_dimensiones(alto)

        # Registro de los datos recibidos para verificación
        datos_recibidos = {
            "institucion": institucion,
            "worker": worker,
            "ubicacion": ubicacion,  # Nuevo campo
            "registrador": registrador,
            "cod_patr": cod_patr,
            "cod_2024": cod_2024,
            "cod_2023": cod_2023,
            "cod_2022": cod_2022,
            "cod_2021": cod_2021,
            "cod_2020": cod_2020,
            "color": color,
            "material": material,
            "largo": largo_validado,
            "ancho": ancho_validado,
            "alto": alto_validado,
            "marca": marca,
            "modelo": modelo,
            "num_serie": num_serie,
            "ubicacion": ubicacion,  # Nuevo campo
            "num_placa": num_placa,  # Nuevo campo
            "num_chasis": num_chasis,  # Nuevo campo
            "num_motor": num_motor,  # Nuevo campo
            "anio_fabricac": anio_fabricac,  # Nuevo campo
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
            codigo_inv_2022=cod_2022,
            codigo_inv_2021=cod_2021,
            codigo_inv_2020=cod_2020,
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
            ubicacion= ubicacion,  # Nuevo campo
            num_placa= num_placa,  # Nuevo campo
            num_chasis= num_chasis,  # Nuevo campo
            num_motor= num_motor,  # Nuevo campo
            anio_fabricac= anio_fabricac,  # Nuevo campo
            estado=estado,
            en_uso=(enUso == 'Sí'),
            observaciones=observaciones
        )
        db.add(nuevo_bien)
        db.flush()  # Para obtener el ID del bien

        # Procesar y guardar imágenes
        datos_imagenes = {
            'bien_id': nuevo_bien.id,
            'codigo_patrimonial': cod_patr,
            'codigo_inv_2024': cod_2024,
            'proceso_inventario_id': int(registrador),  # O el ID que corresponda
            'registrador': registrador,
            'worker': worker
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


def get_s3_url(key):
    return f"https://d-ex.s3.amazonaws.com/{key}"

@app.get("/dashboard/latest-item")
async def get_latest_inventoried_item(db: Session = Depends(get_db)):
    try:
        # Obtener el último bien inventariado
        latest_item = db.query(Bien).order_by(Bien.id.desc()).first()
        if not latest_item:
            raise HTTPException(status_code=404, detail="No se encontró el último bien inventariado.")

        # Log para verificar el bien obtenido
        print(f"Último bien inventariado: {latest_item}")

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

        # Log para las imágenes obtenidas
        print(f"Imágenes obtenidas desde la BD: {[image.url for image in images]}")

        # Obtener las imágenes del bien con URLs directas
        image_urls = []
        main_image_url = None
        for img in images:
            if img.url:
                # Extraer solo el nombre del objeto (Key) de la URL completa
                s3_key = img.url.replace('https://d-ex.s3.amazonaws.com/', '')
                
                # Crear URL directa
                direct_url = f"https://d-ex.s3.amazonaws.com/{s3_key}"
                
                image_urls.append({"url": direct_url, "tipo": img.tipo})
                if img.tipo == "PANOR":
                    main_image_url = direct_url

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
                "foto": empleado.foto_perfil if empleado and empleado.foto_perfil else "foto-no-hallado.jpeg"
            }
        }

        # Log para verificar la respuesta final antes de enviarla
        print(f"Respuesta generada: {result}")

        return result

    except Exception as e:
        print(f"Error al obtener el último bien inventariado: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener el último bien inventariado.")
    



    ################################################### SIS ################################
    # Rutas
@app.get("/sis", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(
        "sis_index.html",
        {"request": request}
    )

@app.post("/api/register")
async def register_user(user_data: dict, db: Session = Depends(get_db)):
    # Validar que el DNI no sea usado como contraseña
    if user_data["password"] == user_data["dni"]:
        raise HTTPException(status_code=400, detail="La contraseña no puede ser igual al DNI")
    
    # Crear usuario
    db_user = User(
        email=user_data["email"],
        hashed_password=user_data["password"],  # En producción: hash la contraseña
        full_name=user_data["full_name"],
        dni=user_data["dni"],
        role=user_data["role"]
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"message": "Usuario registrado exitosamente"}

@app.post("/api/login")
async def login(credentials: dict, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials["email"]).first()
    if not user or user.hashed_password != credentials["password"]:  # En producción: verificar hash
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    return {"message": "Login exitoso"}

@app.get("/api/stats/{sede}")
async def get_stats(sede: str):
    # Simulación de datos de estadísticas
    stats = {
        "lima": {
            "inventariado": 75,
            "pendiente": 25,
            "total_activos": 1500
        },
        "arequipa": {
            "inventariado": 60,
            "pendiente": 40,
            "total_activos": 800
        },
        "trujillo": {
            "inventariado": 85,
            "pendiente": 15,
            "total_activos": 600
        }
    }
    return stats.get(sede.lower(), {"error": "Sede no encontrada"})

"""
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

"""
