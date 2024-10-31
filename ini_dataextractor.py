# Importaciones necesarias
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
from typing import List
from fastapi import FastAPI, Request, HTTPException, Form, UploadFile, File, Depends
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from utils.dispositivo import determinar_tipo_dispositivo
from database import SessionLocal
from scripts.py.create_tables_BD_INVENTARIO import (
    Base, Bien, RegistroFallido, MovimientoBien, ImagenBien, 
    HistorialCodigoInventario, AsignacionBien, InventarioBien, 
    TipoBien, TipoMovimiento
)
from scripts.py.buscar_por_trabajador_inventario import consulta_registro

try:
    import claves  # Solo se usará en el entorno local
except ImportError:
    pass


# Configuración de FastAPI, OpenAI, y S3
app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
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
@app.post("/upload_fotos")
async def upload_fotos(request: Request, fotos: List[UploadFile] = File(...), uuid: List[str] = Form(...), db: Session = Depends(get_db)):
    form = await request.form()
    
    # Aquí recibimos COD_USUARIO y COD_EMPLEADO desde el formulario
    cod_usuario = form.get('cod_usuario')
    cod_empleado = form.get('cod_empleado')

    #proceso_inventario_id = int(form.get('proceso_inventario_id'))  # Obtener el proceso de inventario
    proceso_inventario_id = 9999  # Obtener el proceso de inventario

    fotos = form.getlist("fotos")
    uuid = form.getlist("uuid")
    datos_combinados = {
        "INV_Patrim": "No disponible",
        "INV_2024": "No disponible",
        "INV_2023": "No disponible",
        "INV_2021": "No disponible",
        "INV_2019": "No disponible",
        "Marca": "No disponible",
        "Modelo": "No disponible",
        "N_Serie": "No disponible",
        "Color": "No disponible",
        "Material": "No disponible",
        "Descripcion": "No disponible"
    }

    

    image_contents = []
    for foto in fotos:
        file_content = await foto.read()
        if len(file_content) == 0:
            raise ValueError(f"El archivo {foto.filename} está vacío")

        resized_image = resize_image(file_content)
        base64_image = base64.b64encode(resized_image).decode("utf-8")
        image_contents.append(base64_image)

        tipo_imagen = "PANOR" if "Descripcion" in datos_combinados else "OTROS"
        filename = generate_image_filename(cod_usuario, cod_empleado, tipo_imagen, "INV_2024")
        
        s3_url = upload_image_to_s3(resized_image, filename)
        print(f"URL de S3 generada: {s3_url}")  # Confirmación de URL generada

        # Depuración antes de invocar `registrar_imagen_en_db`
        print(f"Llamando a `registrar_imagen_en_db` con bien_id={cod_usuario}, proceso_inventario_id={proceso_inventario_id}, s3_url={s3_url}, descripcion={tipo_imagen}")
        registrar_imagen_en_db(db=db, bien_id=cod_usuario, proceso_inventario_id=proceso_inventario_id, s3_url=s3_url, descripcion=tipo_imagen)

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
                "INV_2024": "valor o No disponible",
                "INV_2023": "valor o No disponible",
                "INV_2021": "valor o No disponible",
                "INV_2019": "valor o No disponible",
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

# --------------------------------------------------------------
# Endpoint para Registrar un Nuevo Bien y Poblar Tablas Relacionadas
# --------------------------------------------------------------
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
    try:
        # Registro de los datos recibidos para la verificación
        print("Datos recibidos para registrar bien:")
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
        print(json.dumps(datos_recibidos, indent=4))

        # Verificación de existencia para evitar duplicados
        bien_existente_patrim = db.query(Bien).filter(Bien.codigo_patrimonial == cod_patr).first()
        if bien_existente_patrim:
            raise ValueError("Código patrimonial duplicado")

        bien_existente_2024 = db.query(Bien).filter(Bien.codigo_inv_2024 == cod_2024).first()
        if bien_existente_2024:
            raise ValueError("Código de inventario 2024 duplicado")

        # Registro del bien en caso de no existir duplicados
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
        db.commit()

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

        return JSONResponse(content={"exito": True, "mensaje": "Bien registrado y asignado correctamente"})

    except ValueError as e:
        db.rollback()
        error_message = "El código patrimonial ya existe en el sistema." if "patrimonial" in str(e) else "El código de inventario 2024 ya existe en el sistema."
        print(f"Error de validación: {error_message}")
        
        # Registro en la tabla de fallos
        registro_fallido = RegistroFallido(
            datos_bien=json.dumps(datos_recibidos),
            error=error_message,
            inventariador_id=registrador,
            institucion_id=institucion,
            responsable_id=worker
        )
        db.add(registro_fallido)
        db.commit()

        return JSONResponse(content={"exito": False, "error": error_message}, status_code=400)

    except Exception as e:
        db.rollback()
        error_message = "Error al registrar bien en el sistema. Inténtalo de nuevo o contacta al soporte."
        print(f"Error inesperado: {str(e)}")
        
        # Registro en la tabla de fallos
        registro_fallido = RegistroFallido(
            datos_bien=json.dumps(datos_recibidos),
            error=str(e),
            inventariador_id=registrador,
            institucion_id=institucion,
            responsable_id=worker
        )
        db.add(registro_fallido)
        db.commit()

        return JSONResponse(content={"exito": False, "error": error_message}, status_code=500)


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