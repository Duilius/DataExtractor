from openai import OpenAI
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
from fastapi.responses import RedirectResponse,Response,FileResponse, HTMLResponse
from fastapi import APIRouter, Response, Header, Form, Path, UploadFile

from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

##Importing the Modules Needed to Extract Text with Google Artificial Intelligence

from google.cloud import documentai
from google.api_core.client_options import ClientOptions
import os, json
import claves # Archivo con las claves de acceso a la API de DocumentAI

## Variables de conexión a Base de Datos en Railway
db_user=os.getenv("DB_USER")
db_password=os.getenv("DB_PASSWORD")
db_host=os.getenv("DB_HOST")
db_port=os.getenv("DB_PORT")
db_name=os.getenv("DB_NAME")
db_type=os.getenv("DB_TYPE")



from utils.dispositivo import determinar_tipo_dispositivo

app=FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount( "/static" , StaticFiles(directory="static"), name="static")

# --------------------------------------------------------------
# Load DNI Extractor - Home
# --------------------------------------------------------------

@app.get('/')
async def root(request:Request):
    
    return templates.TemplateResponse("ini-dataextractor.html", {'request':request}, media_type="text/html")

# --------------------------------------------------------------
# Recibe ancho de pantalla (al cargar o al redimensionar)
# --------------------------------------------------------------
@app.route("/cambiar_contenido", methods=["POST"] )
#async def cambiar_contenido(request: Request, datos: dict):
async def cambiar_contenido(request: Request):
    datos = await request.json()
    ancho_pantalla = datos.get("ancho", 0)
    tipo_dispositivo = determinar_tipo_dispositivo(ancho_pantalla)
   
    return templates.TemplateResponse(f"index-{tipo_dispositivo}.html", {'request':request}, media_type="text/html")
        
    #except Exception as e:
    #        print("qué será =====> ", e)
    #        raise HTTPException(status_code=500, detail=str(e))


# --------------------------------------------------------------
# DNI-EXTRACTOR: Maneja rutas
# --------------------------------------------------------------

@app.get('/dni')
async def root(request:Request):
    
    return templates.TemplateResponse("dniextractor/ini-dni.html", {'request':request}, media_type="text/html")


@app.route("/contenido_dni", methods=["POST"] )
async def contenido_dni(request: Request):

    datos = await request.json()
    ancho_pantalla = datos.get("ancho", 0)
    tipo_dispositivo = determinar_tipo_dispositivo(ancho_pantalla)
        
    return templates.TemplateResponse(f"dniextractor/dni-{tipo_dispositivo}.html", {'request':request}, media_type="text/html")


# --------------------------------------------------------------
# FAC-EXTRACTOR: Maneja rutas
# --------------------------------------------------------------

@app.get("/facturas")
async def root(request:Request):
    
    return templates.TemplateResponse("facextractor/ini-fac.html", {'request':request}, media_type="text/html")

@app.route("/contenido_fac", methods=["POST"] )
async def contenido_fac(request: Request):

    datos = await request.json()
    ancho_pantalla = datos.get("ancho", 0)
    tipo_dispositivo = determinar_tipo_dispositivo(ancho_pantalla)
        
    return templates.TemplateResponse(f"facextractor/fac-{tipo_dispositivo}.html", {'request':request}, media_type="text/html")

# --------------------------------------------------------------
# INF-EXTRACTOR: Maneja rutas
# --------------------------------------------------------------

@app.get("/info-extractor")
async def root(request:Request):
    
    return templates.TemplateResponse("infextractor/ini-inf.html", {'request':request}, media_type="text/html")

@app.route("/contenido_inf", methods=["POST"] )
async def contenido_inf(request: Request):

    datos = await request.json()
    ancho_pantalla = datos.get("ancho", 0)
    tipo_dispositivo = determinar_tipo_dispositivo(ancho_pantalla)
        
    return templates.TemplateResponse(f"infextractor/inf-{tipo_dispositivo}.html", {'request':request}, media_type="text/html")


# --------------------------------------------------------------
# Recibe "src" del Video de DEMOSTRACIÓN a Cargar
# --------------------------------------------------------------
@app.get("/videos-demo")
async def video_demo(request: Request, origen:str ):
    #origen = request.query_params.get("origen")
    
    print("Origen del Video", origen)
    
    # Construct the video source URL based on the selected option
    #src_video = f"/static/videos-demo/{origen}.mp4"

        
    print("Video sobre ======> XXXXXXXXX", type(origen))
    
    return templates.TemplateResponse("videos-demo.html", {'request':request, "origen":origen})
        
    

# --------------------------------------------------------------
# Recibe Datos de Registro Nuevo Usuario - Prueba
# --------------------------------------------------------------

@app.post('/newUser/')
async def new_user(request:Request, countryCode:str= Form(),numWa:str= Form(),nombre:str= Form(), consulta:str=Form()):
    print("el nombre es ----------- ", nombre)
    if len(nombre) > 3:

        print("Código País ===> ", countryCode)
        print("N° WhatsApp ===> ", numWa)
        print("Nombres ===> ", nombre)
        print("Consulta ===> ", consulta)
        #print("La Clave ===> ", clave)

        return RedirectResponse("/servicios")
    else:
        print('muy corto =========== ', nombre)

@app.post('/servicios')
async def servicios(request:Request):

    return templates.TemplateResponse("servicios-extraccion-datos.html",{'request':request})

#Tipos de Servicio: DNI, Recetas, Listas Compra, Inventario, Facturas, Reconoc Facial
@app.get('/extractorde')
async def extractorDe(request:Request, tiposervicio:str=""):
    print("Tipo de Servicio elegido: ", tiposervicio)

    return templates.TemplateResponse("demo/"+tiposervicio+"_demo.html", {'request':request})
    
    #Hay un archivo por cada tipo de Servicio  <===
    #En el caso de INVENTARIO: las imágenes cargadas/tomadas las procesa la ruta ==>> /upload_fotos


### SERVICIO: INVENTARIO #### 👈👈👈
@app.post("/upload_fotos")
async def upload_fotos(request: Request, fotos: List[UploadFile]):

    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
        return encoded_string

    script_directory = os.path.dirname(os.path.abspath(__file__))
    client = OpenAI(api_key="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")


    ## Variables de entorno - Servicio de Google Cloud
    endpoint = os.getenv('ENDPOINT')
    project_id = os.getenv('PROJECT_ID')
    processor_id = os.getenv('PROCESSOR_ID') # Create processor in Cloud Console
    location = os.getenv('REGION') # Format is 'us' or 'eu'

    #Create an instantiate to "DocumentProcessorServiceClient" class
    client = documentai.DocumentProcessorServiceClient(
            client_options=ClientOptions(api_endpoint=f"{location}-{endpoint}"))

    #Get processor path
    name = client.processor_path(project_id, location, processor_id)

    carpeta_pdf = getcwd() + "/templates/image"

    for file_uri in fotos:

        #Get mime_type
        if file_uri.filename.endswith('.pdf'):
            mime_type = "application/pdf"
        elif file_uri.filename.endswith('.jpg') or file_uri.filename.endswith('.jpeg'):
            mime_type = "image/jpeg"
        elif file_uri.filename.endswith('.png'):
            mime_type = "image/png"
        else:
            # Establecer un valor predeterminado en caso de que no se encuentre ninguna extensión compatible
            mime_type = "application/octet-stream"  # Tipo MIME genérico para datos binarios

        lectura_archivo=""

        try:
            with open(file_uri.filename, 'rb') as file_bites:
                file_content_bites = file_bites.read()
                # Procesar el contenido del archivo, como guardar en una base de datos o realizar operaciones adicionales
                lectura_archivo="OK"

                #Create a "RawDocument" object (encapsulate the file content + mime_type)
                raw_file_documentai = documentai.RawDocument(
                    content=file_content_bites,
                    mime_type=mime_type)

                #Request to process the document (raw_file_documentai)
                request_doc = documentai.ProcessRequest(
                    name=name,
                    raw_document=raw_file_documentai)   
                
                #Request the document to be processed and receive the response
                response = client.process_document(request=request_doc)
                document = response.document #Get the document object, already processed, from the response
                
                print("EL resultado es ===> ", document)

                #Validate and Filter each document 👀
                ###cabezera,json_data = filter_document(document)

                #Insert the document into the database
                ###mto_pagado, num_operacion = save_storage(cabezera,json_data)

                #print("MONTO PAGADO ================>", mto_pagado)
                #print("OERACION N°  ================>", num_operacion)

                #Return the result of query
                ###results, count_result = show_table_yape()

                #Return the result of the insertion
                ###print("Monto pagado: S/. ", mto_pagado)
                ###print("Número de operación: ", num_operacion)	
                ###return templates.TemplateResponse("partial_yape.html", {"request": request,"yapes": results, "toal_yapes_hoy": count_result, "lectura_archivo":lectura_archivo})

        except FileNotFoundError:
            # Manejar el caso cuando el archivo no se encuentra
            lectura_archivo="No-hallado"
            return templates.TemplateResponse("partial_yape.html", {"request": request, "lectura_archivo":lectura_archivo})
        except IOError as e:
            # Manejar otras excepciones de lectura/escritura
            lectura_archivo=e
            return templates.TemplateResponse("partial_yape.html", {"request": request, "lectura_archivo":lectura_archivo})