import os
import asyncio
from typing import Optional, List
import uvicorn
import fastapi
from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi import APIRouter, Response, Header, Form, Path

from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

apiDni=FastAPI()

templates = Jinja2Templates(directory="../../templates/html")
apiDni.mount( "/static" , StaticFiles(directory="../../templates/"), name="static")

# --------------------------------------------------------------
# Load DNI Extractor - Home
# --------------------------------------------------------------

@apiDni.get('/')
async def Claves(request:Request):
    context = {'request':request}
    return templates.TemplateResponse("diseno1.html", context)


# --------------------------------------------------------------
# Recibe Datos de Registro Nuevo Usuario - Prueba
# --------------------------------------------------------------

@apiDni.post('/newUser/')
async def new_user(request:Request, countryCode:str= Form(),numWa:str= Form(),nombre:str= Form(),clave:str= Form()):
    print("el nombre es ----------- ", nombre)
    if len(nombre) > 3:

        print("Código País ===> ", countryCode)
        print("N° WhatsApp ===> ", numWa)
        print("Nombres ===> ", nombre)
        print("La Clave ===> ", clave)
    else:
        print('muy corto =========== ', nombre)