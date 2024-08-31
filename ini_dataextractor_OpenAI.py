from openai import OpenAI
import json
import base64
import os
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

    for foto in fotos:
        # Guardar la imagen localmente en el servidor
        photo_path = os.path.join(script_directory, foto.filename)
        with open(photo_path, "wb") as photo_file:
            photo_file.write(await foto.read())

        # Codificar la imagen como Base64 y construir la URL
        image_url = f"data:image/jpeg;base64,{encode_image(photo_path)}"

        # Enviar la imagen a OpenAI
        response = client.chat.completions.create(
            model='gpt-4-vision-preview',
            messages=[
                {   
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extraer la información del documento proporcionado, incluyendo el color principal del objeto:\n"
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url}
                        }
                    ],
                }
            ],
            max_tokens=600,
        )

        response_text = response.choices[0].message.content
        
        #Pedimos que formatee el texto a lo que se necesita:
        #CodPatrimonial ===> No tiene guión "-"
        #Cod 2023: 
        #Cod 2021:
        #Cod 2019:
        #Color:
        response2 = client.chat.completions.create(
            model='gpt-4-turbo-2024-04-09',
            messages=[
                {"role":"system", "content":[
                    {
                        "type":"text",
                        "text":"Ofréceme los datos numéricos de las Etiquetas CORPAC S.A., INV. 2023, INV, 2021, INV. 2019 e INV. 2021"
                    }
                ]
                 },
                { "role": "user",
                  "content":[
                        {
                            "type": "text",
                            "text": response_text
                        }
                  ]
                }
                ],
            max_tokens=20
        )
        
        print("Respuesta de OpenAI-2:", response2)
        print("Respuesta de OpenAI-1:", response_text)
        #Aquí le pedimos a CHATGPT que interprete y clasifique los datos


        # Procesar la respuesta de OpenAI
        """
        try:
            json_string = response.choices[0].message.content
            json_string = json_string.replace("```json\n", "").replace("\n```", "")
            json_data = json.loads(json_string)
        except (IndexError, json.JSONDecodeError) as e:
            print(f"Error al procesar la respuesta de OpenAI: {e}")
            continue

        # Guardar los datos JSON en un archivo
        filename_without_extension = os.path.splitext(os.path.basename(photo_path))[0]
        json_filename = f"{filename_without_extension}.json"
        json_path = os.path.join(script_directory, "Data", json_filename)

        try:
            with open(json_path, 'w') as file:
                json.dump(json_data, file, indent=4)
                print(f"Datos JSON guardados en {json_path}")
        except Exception as e:
            print(f"Error al guardar los datos JSON: {e}")
        """

    #return {"message": "Proceso completado"}