#import pytesseract
import numpy as np
import cv2
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
from fastapi import APIRouter, Form, UploadFile

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
    print("Se busca a : ====> ", busca_usuario)
    valor = busca_usuario
    users =consulta_registro(valor)
    print("Resultado =====>", users)

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
    #return templates.TemplateResponse("demo/inv_demo.html", {'request': request})
    return templates.TemplateResponse("demo/inventario_activos2.html", {'request': request})
    #return templates.TemplateResponse("demo/inv_demo_old_old.html", {'request': request})

@app.get('/fotos')
async def fotos(request: Request):
    #return templates.TemplateResponse("demo/inv_demo.html", {'request': request})
    return templates.TemplateResponse("demo/foto_voz.html", {'request': request})

#PROCESA ARCHIVOS HTML (area_search.html y worker_search.html) contenidos en modal (.modal)
#al hacer clic en botones: BUSCAR POR AREA o BUSCAR POR TRABAJADOR
@app.get("/templates/{path:path}")
async def serve_template(request: Request, path: str):
    return templates.TemplateResponse(path, {"request": request})


# --------------------------------------------------------------
# SERVICIO: INVENTARIO
# --------------------------------------------------------------

# Inicializar el cliente de OpenAI
client = OpenAI(api_key=os.getenv("inventario_demo_key"))

# Función para codificar la imagen en base64
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

import json
import re


import json
import re
import os
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from openai import OpenAIError  # Asegúrate de tener la importación correcta para errores



def clean_value(value):
    """Limpia los valores para asegurar que sean válidos en el JSON"""
    if isinstance(value, str):
        # Elimina comas o puntos problemáticos, o trunca si es necesario
        return value.replace(',', '').replace('.', '').strip()[:50]  # Limitar a 50 caracteres
    return value

def merge_dicts(dict1, dict2):
    """Combina dos diccionarios según las reglas definidas."""
    combined = dict1.copy()  # Copiar el primer diccionario

    for key, value in dict2.items():
        value = clean_value(value)  # Limpiar el valor antes de fusionar
        if value != "No aplica":
            if combined[key] == "No aplica":
                combined[key] = value

    return combined

@app.post("/upload_fotos")
async def upload_fotos(fotos: List[UploadFile]):
    if not client.api_key:
        raise HTTPException(status_code=500, detail="La clave de API de OpenAI no se ha encontrado en las variables de entorno.")

    # Diccionario combinado inicializado
    datos_combinados = {
        "Cod. Patrim": "No aplica",
        "Cod. 2023": "No aplica",
        "Cod. 2021": "No aplica",
        "Marca": "No aplica",
        "Modelo": "No aplica",
        "N Serie": "No aplica",
        "Color": "No aplica",
        "Descripción": "No aplica"
    }

    for foto in fotos:
        try:
            # Guardar y procesar imagen
            photo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), foto.filename)
            with open(photo_path, "wb") as photo_file:
                photo_file.write(await foto.read())

            image_base64 = encode_image(photo_path)

            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """
                            A continuación, se te proporcionarán varias imágenes que contienen etiquetas de inventario de bienes. Extrae la información en el siguiente formato de diccionario sin agregar texto explicativo ni comentarios adicionales. Solo proporciona la estructura del diccionario y asegúrate de que esté bien formateado como JSON:

                            diccionario = {
                                "Cod. Patrim": valor extraído,
                                "Cod. 2023": valor extraído,
                                "Cod. 2021": valor extraído,
                                "Marca": valor extraído,
                                "Modelo": valor extraído,
                                "N Serie": valor extraído,
                                "Color": valor extraído,
                                "Descripción": valor extraído
                            }

                            Considera las siguientes reglas:
                            1. El primer valor del diccionario corresponderá al Código Patrimonial, el cual nunca tiene guiones y nunca es igual a ningún otro código en ninguna de las etiquetas. Esta etiqueta no indica el año ni las palabras "inventario", "INV" ni ninguna referencia a ello. Es decir, no puede haber un código patrimonial (campo Cod. Patrim.)que contenga un guion, ni estar prcedido o titulado, ni nada parecido, con los términos INVENTARIO, INV., INVENT., etc.
                            2. Los campos "Cod. 2023" y "Cod. 2021" siempre tienen un guión.
                            3. No siempre están presentes en una imagen la "Marca", el "Modelo", ni el "N de Serie".
                            4. El colorsiempre extraelo y prioriza el de la imagen que capta el objeto completo o de la foto panorámica.
                            5. La descripción debe corresponder con la de la imagen panorámica y/o la que muestre el objeto principal y/o de mayor tamaño que se aprecie en la foto.
                            6. Para el año 2023, la etiqueta debe contener "INV. 2023".
                            7. Para el año 2021, la etiqueta debe contener "INV. 2021".
                            8. Si algún dato contiene comas, puntos, o elementos que puedan causar problemas en la construcción del JSON, trunca el dato o simplifícalo.
                            9. Si no se encuentra un dato o hay duda, escribe "No Aplica" en su lugar.
                            10. Si se procesan varias imágenes, combina los datos en un único diccionario sin duplicados y sin campos innecesarios.
                            
                            Responder solo con el siguiente formato:
                            
                            diccionario = {
                                "Cod. Patrim": valor extraído,
                                "Cod. 2023": valor extraído,
                                "Cod. 2021": valor extraído,
                                "Marca": valor extraído,
                                "Modelo": valor extraído,
                                "N Serie": valor extraído,
                                "Color": valor extraído,
                                "Material": valor extraído,
                                "Descripción": valor extraído
                            }

                            Esto es importantísimo: al diccionario ofrecido le darás el nombre diccionario. 

                            Intenta siempre describir la imagen para darle valor al campo "Descripción", siempre y cuando tengas visión completa del objeto principal de la imagen.

                            Recuerda que este reconocimiento es respecto a objetos o bienes y que no interesan los espacios o ambientes en que estos encuentran. Es decir, fíjate, enfoca o concéntrate en el objeto de mayor volumen o tamaño; ese es el objeto que debes describir.

                            El resultado debe ser un diccionario JSON sin explicaciones adicionales, solo los datos solicitados. Siempre debes devolver un JSON válido, incluso si alguna de las imagenes no tiene ninguna etiqueta y/o es necesario truncar o procesar parcialmente los datos.

                            Si tienes dificultad, poca información, escasa o nula fiabilidad o duda para darle valor a un campo, asignale el valor "No Aplica", pero SIEMPRE DEVUELVE UN JSON VÁLIDO.
                            Si debes truncar o no puedes interpretar alguno de los campos, simplemente le asignas el valor "No Aplica", pero DEVUELVE o RESPONDE SIEMPRE con un Json válido.
                            """
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ]

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=300
            )

            response_text = response.choices[0].message.content.strip()

            if not response_text:
                raise ValueError("La respuesta de GPT-4 Vision está vacía")

            # Extracción del bloque JSON usando expresiones regulares
            json_match = re.search(r"\{.*?\}", response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                try:
                    response_dict = json.loads(json_str)  # Validar JSON
                except json.JSONDecodeError:
                    raise ValueError("La respuesta no es un JSON válido")

                # Combinar los datos en el diccionario final
                datos_combinados = merge_dicts(datos_combinados, response_dict)
            else:
                raise ValueError("La respuesta no contiene un JSON válido")

        except ValueError as e:
            return JSONResponse(content={"status": "error", "detail": str(e)}, status_code=500)
        except OpenAIError as e:
            return JSONResponse(content={"status": "error", "detail": f"Error al procesar la imagen: {str(e)}"}, status_code=500)
        except Exception as e:
            return JSONResponse(content={"status": "error", "detail": f"Error inesperado: {str(e)}"}, status_code=500)
        finally:
            if os.path.exists(photo_path):
                os.remove(photo_path)

    # Asegurarnos de devolver correctamente el diccionario combinado
    # Imprimir el diccionario combinado en la terminal
    print(datos_combinados)

    # Asegurarnos de devolver correctamente el diccionario combinado
    return JSONResponse(content={"diccionario": datos_combinados}, status_code=200)
