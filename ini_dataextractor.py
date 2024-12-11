# Importaciones necesarias
from pydantic import BaseModel
from middleware.auth_middleware import AuthMiddleware
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
from typing import List, Dict, Optional
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
#from create_tabla_inventario_anterior import InventarioAnterior
from scripts.sql_alc.anterior_sis import AnteriorSis
from auth_routes import auth_router
from scripts.sql_alc.auth_models import Usuario  # Cambiamos User por Usuario que es el nombre que usamos
from office_routes import office_router
from scripts.py.auth_utils import AuthUtils
from config import JWT_SECRET_KEY
from dashboard_routes import dashboard_router
from admin_routes import admin_router
from starlette.requests import Request
from scripts.py.utils import obtener_id_usuario, obtener_id_empleado
from proveedor_routes import proveedor_router
from area_routes import area_router
from scripts.sql_alc.crea_estructura_base import crear_estructura_areas

from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

try:
    import claves  # Solo se usará en el entorno local
except ImportError:
    pass


# Configuración de FastAPI, OpenAI, y S3
app = FastAPI(max_form_memory_size=50 * 1024 * 1024)  # 50 MB



# Configurar límites de tamaño
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar límite de tamaño del servidor
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        limit_concurrency=1000,
        limit_max_requests=1000,
        timeout_keep_alive=0,
        http='h11',
        loop='auto',
        reload=True,
        server_header=True,
        date_header=True,
        proxy_headers=True,
        forwarded_allow_ips='*',
        client_max_size=1024*1024*50  # 50MB máximo total
    )
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# Configuración del límite de tamaño de solicitud
from fastapi.middleware.cors import CORSMiddleware
#from starlette.datastructures import UploadFile


# Primero los templates y static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Después de crear la app FastAPI y antes de cualquier ruta
from starlette.middleware.sessions import SessionMiddleware

# Después los middlewares en orden
app.add_middleware(AuthMiddleware)
app.add_middleware(
    SessionMiddleware,
    secret_key=secrets.token_urlsafe(32),
    session_cookie="inventario_session"
)

# Finalmente los routers
app.include_router(office_router)
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(admin_router)
app.include_router(proveedor_router)  # Añadimos el nuevo router
app.include_router(area_router)

s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

client = OpenAI(api_key=os.getenv("inventario_demo_key"))
BUCKET_NAME = "d-ex"
MAX_IMAGE_SIZE = (2048, 2048)

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
    return f"SIS-{cod_usuario}-{cod_empleado}-{tipo_imagen}-{inv_2024}.jpg"


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
        ubicacion = form.get('area_search', '')
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
    try:
        access_token = request.cookies.get("access_token")
        print(f"Token recibido: {access_token}")
        
        if not access_token:
            print("No hay token de acceso")
            return RedirectResponse(url="/auth/login", status_code=302)
        
        auth_utils = AuthUtils(JWT_SECRET_KEY)  # Usar la constante
        try:
            payload = auth_utils.verify_access_token(access_token)
            print(f"Token verificado exitosamente: {payload}")
            return templates.TemplateResponse("demo/inventario_sis.html", {'request': request})
        except Exception as token_error:
            print(f"Error verificando token: {str(token_error)}")
            return RedirectResponse(url="/auth/login", status_code=302)
            
    except Exception as e:
        print(f"Error general en /demo-inventario: {str(e)}")
        return RedirectResponse(url="/auth/login", status_code=302)

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
def optimize_image(image_data: bytes, format: str = 'webp') -> bytes:
    try:
        with Image.open(io.BytesIO(image_data)) as img:
            # Convertir a RGB si es necesario
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.getchannel('A'))
                img = background

            # Redimensionar si excede límites - como antes
            if img.size[0] > 1024 or img.size[1] > 1024:
                img.thumbnail((1024, 1024))  # Sin LANCZOS

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

    Si ves códigos de inventario:
    - Extráelos usando las claves 'inv_2023', 'inv_2022', 'codigo_SBN', 'cod_patr'

    - "codigo_SBN": Códigos de exactamente 12 digitos, precedido de "SBN:"
    - "inv_2023": Códigos de exactamente 5 digitos, escrito en fondo blanco con letras negras, que tienen encima el texto "INV 2023".
    - "inv_2022": Códigos de exactamente 5 digitos, escrito en fondo negro con letras blanca, que tienen encima el texto "INV - 2022".
    - "cod_patr": Códigos de 4 o 5 digitos dispuestos en forma vertical y acompañado de las letras "CP", en forma horizontal o viceversa. Presentes en etiquetas con el texto "SEGURO INTEGRAL DE SALUD"
    - Si ves el objeto completo (no solo etiquetas o detalles):
    - "descripcion_IA": Una muy breve descripción del objeto sin comentar objetos encima ni al rededor. Incluir color principal y material.

    IMPORTANTE:
    - Si ves claramente etiquetas de inventario, NO describas la etiqueta misma ni la superficie donde están pegadas.
    - NO incluyas descripción, color o material si solo ves etiquetas o números.
    - Incluye SOLO las claves necesarias según las reglas anteriores.
    - La respuesta debe ser un JSON válido con comillas dobles.

    Ejemplo si solo ves etiquetas:
    {
        "codigo_SBN": "74641240062",
        "inv_2023": "03234",
        "inv_2022": "05123",
        "cod_patr": "2173"
    }

    Ejemplo si ves el objeto completo:
    {
        "descripcion-IA": "Archivador de melamina con puertas de vidrio, color blanco"
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
    Prioridad: codigo_SBN > inv_2024 > cod_patr > inv_2023
    """
    print(f"Determinando tipo de imagen para datos: {datos_extraidos}")
    
    # Si tiene número de serie, es SERIE
    #if 'N_Serie' in datos_extraidos and datos_extraidos['N_Serie'] != "No disponible":
    #    return 'SERIE'
    
    # Si tiene descripción-IA, es PANOR
    if 'descripcion-IA' in datos_extraidos and datos_extraidos['descripcion-IA'] != "No disponible":
        return 'PANOR'
    
    # Si tiene algún código de inventario, es CODIG
    inv_prefixes = ['inv_', 'codigo_', 'cod_patr']
    for key in datos_extraidos:
        if any(key.startswith(prefix) for prefix in inv_prefixes):
            if datos_extraidos[key] != "No disponible":
                return 'CODIGO'
    
    return 'OTRO'


def generar_nombre_imagen(cod_usuario: str, cod_empleado: str, tipo: str, inv_2024: str, codigo_SBN: str, inv_2023: str, codigo_patr: str, num_imagen: int = None) -> str:
    """
    Genera el nombre final de la imagen según su tipo
    """
    if tipo == 'CODIG' and num_imagen is not None:
        return f"SIS-codUsuario-{cod_usuario or 'No'}-codEmpleado-{cod_empleado or 'No'}-tipo-{tipo or 'No'}-inv2023-{inv_2023 or 'No'}-inv2024-{inv_2024 or 'No'}-codigoSBN-{codigo_SBN or 'No'}-codigoPatr-{codigo_patr or 'No'}-numImagen-{num_imagen or 'N/A'}.webp"

    return f"SIS-codUsuario-{cod_usuario or 'No'}-codEmpleado-{cod_empleado or 'No'}-tipo-{tipo or 'No'}-inv2023-{inv_2023 or 'No'}-inv2024-{inv_2024 or 'No'}-codigoSBN-{codigo_SBN or 'No'}-codigoPatr-{codigo_patr or 'No'}.webp"

# Inicialización del estado de la aplicación para almacenar imágenes en memoria
app.state.imagenes_procesadas = {}


def buscar_en_inventario(db: Session, valor: str, campo: str):
    """
    Busca en la base de datos un registro basado en el campo y valor proporcionados.
    """
    try:
        if campo == "inv_2023":
            print("que hay ====>", db.query(AnteriorSis).filter_by(inv_2023=valor).first().codigo_dni)
            return db.query(AnteriorSis).filter_by(inv_2023=valor).first()
        elif campo == "codigo_SBN":
            return db.query(AnteriorSis).filter_by(codigo_nacional=valor).first()
        elif campo == "cod_patr":
            return db.query(AnteriorSis).filter_by(codigo_patrimonial=valor).first()
        elif campo == "inv_2022":
            return db.query(AnteriorSis).filter_by(inv_2022=valor).first()
        else:
            return None
    except Exception as e:
        print(f"Error en la búsqueda: {e}")
        return None



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


#********************* AREAS OFICIALES PARA EL SELECT *********************************
@app.get("/get-area-nombre/{area_id}")
async def get_area_nombre(area_id: str, db: Session = Depends(get_db)):
    result = db.execute(
        text("SELECT nombre FROM areas_oficiales WHERE id = :area_id"),
        {"area_id": area_id}
    ).first()
    return result[0] if result else ""

def busca_areas_oficiales(db:Session):
    #@app.get("/areas-oficiales", response_class=HTMLResponse)
    #async def get_areas_oficiales(request:Request,db: Session = Depends(get_db)):
        #result = db.execute(text("SELECT id, nombre FROM areas_oficiales ORDER BY id")).fetchall()
        areas_oficiales = db.query(crear_estructura_areas)
        
        print("AREAS OFICIALES 111 =========>", areas_oficiales)
        return areas_oficiales
        
    
# Modificar el endpoint upload_fotos existente
@app.post("/upload_fotos")
async def upload_fotos(
    request: Request, 
    fotos: List[UploadFile] = File(..., max_length=1024*1024*10),  # 10MB por archivo
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
            print("Datos extraídos de la imagen:", datos_imagen)  # Verifica que los datos están correctamente extraídos

            
            # Obtener los códigos extraídos
            inv_2023 = datos_imagen.get("inv_2023")
            codigo_SBN = datos_imagen.get("codigo_SBN")
            cod_patr = datos_imagen.get("cod_patr")
            inv_2022 = datos_imagen.get("inv_2022")

            # Priorizar búsqueda en la base de datos
            codigos = {
                "inv_2023": inv_2023,
                "codigo_SBN": codigo_SBN,
                "cod_patr": cod_patr,
                "inv_2022": inv_2022
            }
            print("Diccionario codigos:", codigos)  # Verifica que el diccionario tenga los datos correctos
            for clave in ["inv_2023", "codigo_SBN", "cod_patr", "inv_2022"]:
                print(f"Comprobando clave: {clave}, valor: {codigos[clave]}")  # Verifica el valor de cada clave
                if codigos[clave]:  # Si el valor de la clave no es None ni vacío
                    if codigos[clave].strip():  # Verifica que no sea una cadena vacía
                        print(f"Buscando en la base de datos con {clave}: {codigos[clave]}")
                        resultado = buscar_en_inventario(db, codigos[clave], clave)
                        if resultado:
                            print(f"Resultado encontrado para {clave}: {resultado}")
                            resultados_busqueda.append(resultado)
                            break  # Detenerse si se encontró un resultado
                        else:
                            print(f"No se encontró registro para {clave} con valor {codigos[clave]}")
                    else:
                        print(f"Valor vacío para la clave: {clave}")
                else:
                    print(f"Clave {clave} no tiene valor asignado")



        # Preparar los datos para la plantilla
        datos_para_plantilla = [
            {
                "codigo_patr": dato.codigo_patrimonial or "Sin código patrimonial",
                "codigo_inv_2023": dato.inv_2023 or "No disponible",
                "codigo_inv_2022": dato.inv_2022 or "No disponible",
                "codigo_nacional": dato.codigo_nacional or "No disponible",
                "descripcion": dato.descripcion or "Sin descripción",
                "material": dato.material or "Material no disponible",
                "color": dato.color or "Color no disponible",
                "marca": dato.marca or "Marca no disponible",
                "modelo": dato.modelo or "Modelo no disponible",
                "largo": dato.largo or "Largo no disponible",
                "ancho": dato.ancho or "Ancho no disponible",
                "alto": dato.alto or "Alto no disponible",
                "numero_serie": dato.numero_serie or "N° Serie no disponible",
                "observaciones": dato.observaciones or "Observaciones no disponible",
                "anio_fabricac": dato.anio_fabricac or 0,
                "num_placa": dato.num_placa if dato.num_placa else "Placa no disponible",
                "num_chasis": dato.num_chasis if dato.num_chasis else "N° Chasis no disponible",
                "num_motor": dato.num_motor if dato.num_motor else "N° Serie motor no disponible",
                "procedencia": dato.procedencia if dato.procedencia else "Sin dato",
                "propietario": dato.propietario if dato.propietario else "Sin dato",
                "faltante": dato.faltante if dato.faltante else "Sin dato",
                "sede":  dato.sede if dato.sede else "Sin dato",
                "ubicacion_actual":  dato.ubicacion_actual if dato.ubicacion_actual else "Sin dato",
                "codigo_dni":  dato.codigo_dni if dato.codigo_dni else "Sin dato"
            }
            
            for dato in resultados_busqueda
        ]

        # Almacenar imágenes procesadas
        imagenes_procesadas = {}
        for foto, id_uuid in zip(fotos, uuid):
            file_content = await foto.seek(0)
            file_content = await foto.read()
            imagenes_procesadas[id_uuid] = {
                'contenido': optimize_image(file_content),
                'tipo': 'CODIG',
                'num_imagen': None
            }

        if not hasattr(app.state, 'imagenes_procesadas'):
            app.state.imagenes_procesadas = {}
        app.state.imagenes_procesadas[session_id] = imagenes_procesadas

        # Almacenar información en la sesión
        request.session['imagenes_info'] = {
            uuid: {
                'tipo': info['tipo'],
                'num_imagen': info['num_imagen']
            } for uuid, info in imagenes_procesadas.items()
        }
        print("Resultados de la búsqueda:", resultados_busqueda)  # Verifica los resultados obtenidos

        # **Nuevo código para obtener las áreas de la base de datos**
        areas_oficiales = []
        try:
            areas_result = db.execute(
                text("SELECT id, nombre FROM areas_oficiales ORDER BY id")
            ).fetchall()
            areas_oficiales = [{"id": row[0], "nombre": row[1]} for row in areas_result]

            codigo_dni = datos_para_plantilla[0]["codigo_dni"]

            nombre_empleado = db.execute(
                text("SELECT nombre FROM empleados WHERE codigo = :codigo_dni"),
                {"codigo_dni": codigo_dni}
            ).fetchone()

        except Exception as e:
            print(f"Error obteniendo áreas oficiales: {e}")
        
        return templates.TemplateResponse(
            "demo/datos_inventario_ok.html",
            {"request": request, "datos": datos_para_plantilla,"areas_oficiales": areas_oficiales, "nombre_empleado":nombre_empleado[0], "codigo_dni":codigo_dni}
        )

    except Exception as e:
        print(f"Error inesperado: {e}")
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

    #print("Datos de la IMAGEN >====>", datos)
    #print("Las IMAGENES<<<<<< >====>", imagenes.items())

    try:
        for uuid, imagen_info in imagenes.items():
            tipo = imagen_info['tipo']
            contenido = imagen_info['contenido']

            # Generar nombre final según tipo
            nombre_final = generar_nombre_imagen(
                cod_usuario=datos['registrador'],
                cod_empleado=obtener_id_empleado(db, datos['worker']),
                tipo=tipo,
                inv_2024=datos['codigo_inv_2024'],
                codigo_SBN=datos['codigo_nacional'],
                inv_2023=datos['codigo_inv_2023'],
                codigo_patr=datos['codigo_patrimonial'],
                num_imagen=contador_codig if tipo == 'CODIG' else None
            )


            if tipo == 'CODIG':
                contador_codig += 1

            print("debe grabar )))))", datos["codigo_inv_2024"])
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
    worker: str = Form(...),
    codigoOficina: str = Form(...),  # antes ubicacion
    cod_patr: str = Form(None),
    cod_2024: str = Form(...),
    cod_2023: str = Form(None),
    cod_2022: str = Form(None),
    cod_sbn: str = Form(None),
    #cod_2020: str = Form(None),
    color: str = Form(...),
    material: str = Form(...),
    largo: str = Form(None),
    ancho: str = Form(None),
    alto: str = Form(None),
    marca: str = Form(None),
    modelo: str = Form(None),
    num_serie: str = Form(None),
    #situacion_sis: str = Form(...),  # Nuevo campo
    #situacion_prov: str = Form(...),  # Nuevo campo
    num_placa: str = Form(None),  # Nuevo campo
    num_chasis: str = Form(None),  # Nuevo campo
    num_motor: str = Form(None),  # Nuevo campo
    anio_fabricac: str = Form(None),  # Nuevo campo
    descripcion: str = Form(...),
    observaciones: str = Form(None),
    enUso: str = Form(...),
    estado: str = Form(...),
    acciones: str = Form(None),
    describe_area: str = Form(None),
    area_actual_id: str = Form(None)
):
    #Cookie de USAURIO INVENTARIADOR
    # Acceder a las cookies
    session_cookie = request.cookies.get("session_data")  # Cambia "session" por el nombre real de tu cookie

    if session_cookie:
        # Convertir la cookie de JSON a diccionario
        import json
        try:
            session_data = json.loads(session_cookie)
        except json.JSONDecodeError:
            return {"error": "La cookie de sesión no es válida."}

        # Usar datos de la cookie
        registrador = session_data.get("codigo")
        institucion_id = session_data.get("institucion_id")
        sede_actual_id = session_data.get("sede_actual_id")

        try:
            registrador_id = obtener_id_usuario(db, registrador)
            # Usar inventariador_id en las tablas que lo requieran
        except ValueError as e:
            return JSONResponse(
                content={"exito": False, "error": str(e)},
                status_code=400
            )

    # Obtener el UUID de la cookie
    uuid_imagen = request.cookies.get("imagen_procesada")
    if uuid_imagen:
        # Obtener imágenes del estado de la aplicación
        session_id = request.session.get('id', 'default')
        imagenes = app.state.imagenes_procesadas.get(session_id, {})

        if not imagenes:
            print(f"No hay imágenes en app.state para session_id: {session_id}")
            print(f"Estado actual de app.state.imagenes_procesadas: {app.state.imagenes_procesadas}")
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
            "institucion_id": institucion_id,
            "sede_actual_id": sede_actual_id,
            #"situacion_prov": situacion_prov,
            "custodio_bien": worker,
            "codigo_oficina": codigoOficina,  # Nuevo campo
            "codigo_inventariador": registrador_id,
            "cod_patr": cod_patr,
            "cod_2024": cod_2024,
            "cod_2023": cod_2023,
            "cod_2022": cod_2022,
            "cod_sbn": cod_sbn,
            #"cod_2020": cod_2020,
            "color": color,
            "material": material,
            "largo": largo_validado,
            "ancho": ancho_validado,
            "alto": alto_validado,
            "marca": marca,
            "modelo": modelo,
            "num_serie": num_serie,
            "num_placa": num_placa,  # Nuevo campo
            "num_chasis": num_chasis,  # Nuevo campo
            "num_motor": num_motor,  # Nuevo campo
            "anio_fabricac": anio_fabricac,  # Nuevo campo
            "descripcion": descripcion,
            "observaciones": observaciones,
            "enUso": enUso,
            "estado": estado,
            "acciones":acciones,
            "area_actual_id":area_actual_id,
            "describe_area":describe_area
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
            institucion_id=institucion_id,
            sede_actual_id=sede_actual_id,
            #situacion_prov=situacion_prov,
            codigo_inventariador=registrador_id,
            custodio_bien= worker, #falta programar
            codigo_patrimonial=cod_patr,
            codigo_inv_2024=cod_2024,
            codigo_inv_2023=cod_2023,
            codigo_inv_2022=cod_2022,
            codigo_nacional=cod_sbn,
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
            codigo_oficina= codigoOficina,  # Nuevo campo
            num_placa= num_placa,  # Nuevo campo
            num_chasis= num_chasis,  # Nuevo campo
            num_motor= num_motor,  # Nuevo campo
            anio_fabricac= anio_fabricac,  # Nuevo campo
            estado=estado,
            en_uso=(enUso == 'Sí'),
            observaciones=observaciones,
            acciones=acciones,
            area_actual_id=area_actual_id,
            describe_area=describe_area
        )
        db.add(nuevo_bien)
        db.flush()  # Para obtener el ID del bien

        # Procesar y guardar imágenes
        datos_imagenes = {
            'bien_id': nuevo_bien.id,
            'codigo_patrimonial': cod_patr,
            'codigo_nacional': cod_sbn,
            'codigo_inv_2024': cod_2024,
            'codigo_inv_2023': cod_2023,
            'proceso_inventario_id': registrador_id,  # O el ID que corresponda
            'registrador': registrador_id,
            'worker': worker
        }
        print("DATOS PARA IMAGEN ===>", datos_imagenes)
        resultados_imagenes = await process_and_store_images(imagenes, datos_imagenes, db)

        # Registro de asignación
        asignacion = AsignacionBien(
            bien_id=nuevo_bien.id,
            codigo_patrimonial=cod_patr,
            codigo_inventariador=registrador_id,
            empleado_id=obtener_id_empleado(db,worker),
            proceso_inventario_id=registrador_id,
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
            inventariador_id=registrador_id,
            institucion_id=institucion_id,
            sede_id=sede_actual_id,
            oficina_id=area_actual_id, #codigoOficina
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
            error=error_message,
            inventariador_id=registrador_id,
            institucion_id=institucion_id,
            sede_id=sede_actual_id,
            oficina_id=area_actual_id, #codigoOficina
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
    db_user = Usuario(
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
    user = db.query(Usuario).filter(Usuario.email == credentials["email"]).first()
    if not user or user.hashed_password != credentials["password"]:  # En producción: verificar hash
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    print(f"Token generado: {access_token}")
    print(f"Secret key usado: {os.getenv('JWT_SECRET_KEY')}")
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


# ******************************* CHATBOT **************************

class ChatbotQuery(BaseModel):
    question: str


async def get_session_user(request: Request):
    """Obtiene y valida los datos de sesión del usuario."""
    # Recuperar la cookie de la solicitud
    cookie_data = request.cookies.get("session_data")
    if not cookie_data:
        raise HTTPException(status_code=401, detail="No autorizado: sesión no encontrada.")

    try:
        # Decodificar los datos de sesión desde JSON
        session = json.loads(cookie_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Error al decodificar la sesión.")

    # Validar que contenga los datos requeridos
    if "tipo_usuario" not in session:
        raise HTTPException(status_code=401, detail="No autorizado: tipo de usuario no encontrado.")
    
    return session


@app.get("/chatbot", response_class=HTMLResponse)
async def chatbot_view(request: Request):
    return templates.TemplateResponse("dashboard/shared/chatbot.html", {"request": request})


# ******* CONSULTAS DINÁMICAS **************
@app.post("/chatbot/query")
async def chatbot_query(
    payload: ChatbotQuery,  # Cambiamos de `question: str` a `payload: ChatbotQuery`
    session: dict = Depends(get_session_user)
):
    question = payload.question  # Extraemos la pregunta desde el cuerpo JSON
    tipo_usuario = session["tipo_usuario"]

    # Restringir según el tipo de usuario
    if tipo_usuario == "Comisión Cliente" and "estadísticas" in question.lower():
        return {"response": "No tienes permiso para ver estadísticas."}
    elif tipo_usuario == "Inventariador Proveedor" and "gerencial" in question.lower():
        return {"response": "Este contenido no está disponible para tu perfil."}

    # Si el usuario tiene acceso permitido, procesar la pregunta
    return {"response": "Estamos trabajando en tu respuesta."}
