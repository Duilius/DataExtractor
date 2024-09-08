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

from utils.dispositivo import determinar_tipo_dispositivo

#from scripts.py.claves import inventario_demo_key

from scripts.py.modulo_consulta_registro import consulta_registro
from scripts.py.modulo_graba_registro import graba_registro
from scripts.py.modulo_verify_username import busca_username

import pytesseract
from PIL import Image
import cv2
import numpy as np
import re


## Variables de conexión a Base de Datos en Railway
db_user=os.getenv("DB_USER")
db_password=os.getenv("DB_PASSWORD")
db_host=os.getenv("DB_HOST")
db_port=os.getenv("DB_PORT")
db_name=os.getenv("DB_NAME")
db_type=os.getenv("DB_TYPE")

app=FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount( "/static" , StaticFiles(directory="static"), name="static")

# --------------------------------------------------------------
# Load DNI Extractor - Home
# --------------------------------------------------------------

@app.get('/')
async def root(request:Request):
    
    return templates.TemplateResponse("index-mobile.html", {'request':request}, media_type="text/html")
    #return templates.TemplateResponse("ini-dataextractor.html", {'request':request}, media_type="text/html")

# --------------------------------------------------------------
# Recibe ancho de pantalla (al cargar o al redimensionar)
# --------------------------------------------------------------
@app.route("/cambiar_contenido", methods=["POST"] )
#async def cambiar_contenido(request: Request, datos: dict):
async def cambiar_contenido(request: Request):
    datos = await request.json()
    ancho_pantalla = datos.get("ancho", 0)
    tipo_dispositivo = determinar_tipo_dispositivo(ancho_pantalla)
    
    #return templates.TemplateResponse(f"index-{tipo_dispositivo}.html", {'request':request}, media_type="text/html")
    return templates.TemplateResponse("index-mobile.html", {'request':request}, media_type="text/html")
        
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

        return RedirectResponse(url="https://dataextractor.cloud/servicios", status_code=302)
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



### SERVICIO: INVENTARIO ####
@app.post("/upload_fotos")
async def upload_fotos(request: Request, fotos: List[UploadFile]):
      # Configurar la ruta a Tesseract solo si está en un entorno local (Windows)
    if os.name == 'nt':
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    def detect_orientation_and_text(image_path):
        # Cargar la imagen con OpenCV
        img = cv2.imread(image_path)

        # Convertir la imagen a escala de grises
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Aplicar binarización adaptativa para mejorar la segmentación
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)

        # Detectar contornos que podrían ser etiquetas
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        etiqueta_data = []
        
        for contour in contours:
            # Obtener el bounding box de cada contorno
            rect = cv2.minAreaRect(contour)
            angle = rect[-1]  # El ángulo está en el último valor del rectángulo

            # Clasificar la orientación
            if -10 < angle < 10:
                orientacion = "Horizontal"
            elif 80 < abs(angle) < 100:
                orientacion = "Vertical"
            else:
                orientacion = f"Inclinación de {angle:.2f} grados"

            # Crear una máscara para la etiqueta
            mask = np.zeros_like(gray)
            cv2.drawContours(mask, [contour], -1, (255), -1)
            etiqueta = cv2.bitwise_and(gray, gray, mask=mask)

            # Extraer texto con Tesseract
            texto_etiqueta = pytesseract.image_to_string(etiqueta, lang='spa')

            etiqueta_data.append({
                "orientacion": orientacion,
                "texto": texto_etiqueta.strip()
            })

        return etiqueta_data

    script_directory = os.path.dirname(os.path.abspath(__file__))
    all_etiquetas = []

    for foto in fotos:
        # Guardar la imagen en el servidor
        photo_path = os.path.join(script_directory, foto.filename)
        with open(photo_path, "wb") as photo_file:
            photo_file.write(await foto.read())

        # Procesar la imagen y detectar etiquetas
        etiquetas_detectadas = detect_orientation_and_text(photo_path)
        all_etiquetas.extend(etiquetas_detectadas)

    # Mostrar los resultados en la terminal
    print(f"Total de etiquetas detectadas: {len(all_etiquetas)}")
    for etiqueta in all_etiquetas:
        print(f"Etiqueta: {etiqueta['texto']} | Orientación: {etiqueta['orientacion']}")

    return {"total_etiquetas": len(all_etiquetas), "detalles": all_etiquetas}






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

#######################
# Ruta para verificar si el username existe
#######################
@app.post("/verify-username")
async def verify_username(username:str=Form(...)):
    print("Usuario a loguearse ========>", username)
    data = busca_username(username)
    
    #return JSONResponse(content=response_data)

    print("la data contiene =====>  ", data)

    if data["existe"] == True:
        print("Resultado de búsqueda ==========>", data["id"], " --- Nombres ===>", data["name"])
    else:
        print("usuario no encontrado")

    return RedirectResponse(url="https://dataextractor.cloud/servicios", status_code=302)
@app.get('/blog')
async def blog(request:Request):

    return templates.TemplateResponse("demo/blog.html",{'request':request})



@app.get('/blog-articulo/leer')
async def blog(request: Request, art: str):

    if art=="1":
        pag_articulo ="mejores-herramientas-inventario"
    if art=="2":
        pag_articulo="incumplimiento_inventario"
    if art=="3":
        pag_articulo="razones_inventariar"
    if art=="4":
        pag_articulo="sugerencias_ia_estado"
    if art=="5":
        pag_articulo="sugerencias_5g_estado"

    return templates.TemplateResponse(F"demo/"+pag_articulo+".html",{'request':request})



import os
import uvicorn
from fastapi import FastAPI

app = FastAPI()

# Definiciones de rutas y lógica aquí...

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))  # Usa el puerto de la variable de entorno o el puerto 8000 por defecto
    uvicorn.run("ini_dataextractor:app", host="0.0.0.0", port=port)
