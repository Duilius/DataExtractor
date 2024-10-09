#import pytesseract
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

from io import BytesIO
from PIL import Image  # Añadida esta importación
import boto3
import traceback
import re
import numpy as np
from openai import OpenAI  # Cambié OpenAI por openai
#from openai.types import OpenAIError
from openai import OpenAIError
import json
import base64
import os
from os import getcwd
from urllib.parse import urlparse
import asyncio
from typing import Optional, List
import uvicorn
import fastapi
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, Response, FileResponse, HTMLResponse
from fastapi import APIRouter, Form, UploadFile, File

from fastapi.responses import JSONResponse

from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from utils.dispositivo import determinar_tipo_dispositivo

import claves

from scripts.py.buscar_por_trabajador_inventario import consulta_registro
#from scripts.py.modulo_consulta_registro import consulta_registro
from scripts.py.modulo_graba_registro import graba_registro
from scripts.py.modulo_verify_username import busca_username

## Variables de conexión a Base de Datos en Railway
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")
db_type = os.getenv("DB_TYPE")

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# --------------------------------------------------------------
# Load DNI Extractor - Home
# --------------------------------------------------------------
@app.get('/')
async def root(request: Request):
    return templates.TemplateResponse("index-mobile.html", {'request': request}, media_type="text/html")


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
@app.get("/templates/{path:path}")
async def serve_template(request: Request, path: str):
    if request.url.scheme != 'https':
        return RedirectResponse(request.url.replace(scheme='https'))
    return templates.TemplateResponse(path, {"request": request})


# --------------------------------------------------------------
# SERVICIO: INVENTARIO
# --------------------------------------------------------------
# Inicializar el cliente de OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Inicializar el cliente de S3
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

BUCKET_NAME = "d-ex"
MAX_IMAGE_SIZE = (1024, 1024)

def clean_value(value):
    if isinstance(value, str):
        return value.replace(',', '').replace('.', '').strip()[:50]
    return value

def merge_dicts(dict1, dict2):
    combined = dict1.copy()
    for key, value in dict2.items():
        value = clean_value(value)
        if value != "sindato" and combined[key] == "sindato":
            combined[key] = value
    return combined

def resize_image(image_data: bytes, max_size: tuple) -> bytes:
    with Image.open(BytesIO(image_data)) as img:
        img.thumbnail(max_size)
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

def upload_image_to_s3(file_data: bytes, uuid: str) -> str:
    try:
        s3_filename = f"{uuid}.png"
        s3_client.put_object(Body=file_data, Bucket=BUCKET_NAME, Key=s3_filename)
        return f"https://{BUCKET_NAME}.s3.amazonaws.com/{s3_filename}"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir la imagen a S3: {str(e)}")

@app.post("/upload_fotos")
async def upload_fotos(request: Request, fotos: List[UploadFile] = File(...), uuid: List[str] = Form(...)):
    #print("--- Inicio de la solicitud ---")
    #print(f"Content-Type: {request.headers.get('Content-Type')}")

    
    form = await request.form()
    #print("Form data:", form)
    
    fotos = form.getlist("fotos")
    uuid = form.getlist("uuid")
    
    #print(f"Received {len(fotos)} photos and {len(uuid)} UUIDs")
    
    for i, (foto, id) in enumerate(zip(fotos, uuid)):
        if isinstance(foto, UploadFile):
            content = await foto.read()
            #print(f"Photo {i}: filename={foto.filename}, size={len(content)} bytes, UUID={id}")
            await foto.seek(0)
        else:
            print(f"Photo {i}: type={type(foto)}, UUID={id}")

    if not client.api_key:
        raise HTTPException(status_code=500, detail="La clave de API de OpenAI no se ha encontrado en las variables de entorno.")

    datos_combinados = {
        "INV_Patrim": "No disponible",
        "INV_2023": "No disponible",
        "INV_2021": "No disponible",
        "Marca": "No disponible",
        "Modelo": "No disponible",
        "N_Serie": "No disponible",
        "Color": "No disponible",
        "Material": "No disponible",
        "Descripcion": "No disponible"
    }
    
    image_contents = []
    for index, foto in enumerate(fotos):
        uuid_value = uuid[index]
        file_content = await foto.read()
        
        if len(file_content) == 0:
            raise ValueError(f"El archivo {foto.filename} está vacío")

        resized_image = resize_image(file_content, MAX_IMAGE_SIZE)
        base64_image = base64.b64encode(resized_image).decode("utf-8")
        image_contents.append(base64_image)

        url_imagen = upload_image_to_s3(resized_image, uuid_value)

    try:
        prompt = """
            Analiza las siguientes imágenes y combina la información en un solo diccionario:
            No necesariamente tendrás dos o más imágenes y no necesariamente estarán todos los datos.

            Imagen 1 (Etiquetas): Busca INV. 2021, INV. 2023 y código de 7 dígitos sin guion para el INV_Patrim.
            Imagen 2 (Objeto completo): Proporciona una descripción breve del objeto, su color principal y material.
            Imagen 3 (Detalles): Extrae marca, modelo y número de serie si están presentes.

            Responde SIEMPRE con un diccionario JSON válido en este formato exacto, usando "No disponible" para datos faltantes:
            {
                "INV_Patrim": "valor o No disponible",
                "INV_2023": "valor o No disponible",
                "INV_2021": "valor o No disponible",
                "Marca": "valor o No disponible",
                "Modelo": "valor o No disponible",
                "N_Serie": "valor o No disponible",
                "Color": "valor o No disponible",
                "Material": "valor o No disponible",
                "Descripcion": "Breve descripción del objeto principal"
            }

            Asegúrate de que el JSON sea válido, sin comas al final de la última propiedad y utilizando comillas dobles para las claves y valores.
            Necesariamente debes entregar un solo diccionario, combinando los datos de los demás.
            No incluyas texto ni explicación adicional, solo entrega el diccionario combinado.
            El diccionario combinado solo debe tener una única clave, no puedes repetir claves.
            Un mismo valor no puede repetirse en diferentes claves; ante la duda asigna como valor No disponible.
            """

        messages = [
            {"role": "system", "content": "Eres un asistente experto en toma de inventario de bienes."},
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
            ]}
        ]

        for base64_image in image_contents:
            messages[1]["content"].append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}})

        response = client.chat.completions.create(  
            model="gpt-4-turbo",
            messages=messages,
            max_tokens=300,
            temperature=0,
            top_p=1,
            n=1
        )

        response_text = response.choices[0].message.content.strip()

        if not response_text:
            raise ValueError("La respuesta de GPT-4 está vacía")

        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            try:
                response_dict = json.loads(json_match.group(0))
                datos_combinados.update(response_dict)
            except json.JSONDecodeError as e:
                print(f"Error al decodificar JSON extraído: {e}")
                raise ValueError("No se pudo extraer un JSON válido de la respuesta")
        else:
            raise ValueError("La respuesta no contiene un JSON válido")

        print(f"diccionario= {datos_combinados}")
        return templates.TemplateResponse(
            "demo/datos_inventario_ok.html",
            {"request": request, "datos": datos_combinados}
        )

    except ValueError as e:
        print(f"Error de valor: {str(e)}")
        traceback.print_exc()
        return templates.TemplateResponse(
            "demo/datos_inventario_error.html",
            {"request": request, "error": str(e)}
        )
    except Exception as e:
        print(f"Error inesperado: {str(e)}")
        traceback.print_exc()
        return templates.TemplateResponse(
            "demo/datos_inventario_error.html",
            {"request": request, "error": f"Error inesperado: {str(e)}"}
        )