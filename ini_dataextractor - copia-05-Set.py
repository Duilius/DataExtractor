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
import claves

from scripts.py.modulo_consulta_registro import consulta_registro
from scripts.py.modulo_graba_registro import graba_registro
from scripts.py.modulo_verify_username import busca_username

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


### SERVICIO: INVENTARIO ####
@app.post("/upload_fotos")
async def upload_fotos(request: Request, fotos: List[UploadFile]):
    
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
        return encoded_string

    script_directory = os.path.dirname(os.path.abspath(__file__))
    
    print(os.listdir())  # Para ver si 'claves.py' está en el mismo directorio
    print(dir(claves))   # Para ver qué contiene el módulo 'claves'

    # Usa la clave de la API desde la variable de entorno si está disponible, de lo contrario usa la de claves.py
    #api_key = os.getenv("inventario_demo_key", claves.inventario_demo_key)


    # Invocar la clave de la API desde la variable de entorno
    api_key = os.getenv("inventario_demo_key")

    # Asegurarse de que la clave se haya recuperado correctamente
    if not api_key:
        raise ValueError("La clave de API de OpenAI no se ha encontrado en las variables de entorno.")

    client = OpenAI(api_key=api_key)

    for foto in fotos:
        # Guardar la imagen localmente en el servidor
        photo_path = os.path.join(script_directory, foto.filename)
        with open(photo_path, "wb") as photo_file:
            photo_file.write(await foto.read())

        # Codificar la imagen como Base64 y construir la URL
        image_url = f"data:image/jpeg;base64,{encode_image(photo_path)}"

        # Enviar la imagen a OpenAI
        response = client.chat.completions.create(
            model='gpt-4o',
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

    return RedirectResponse("/servicios")
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