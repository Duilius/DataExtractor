# Usar una imagen base de Python
FROM python:3.11-slim

# Crear un directorio para la aplicación
WORKDIR /app

# Copiar los archivos de requisitos y la aplicación
COPY requirements.txt /app/
COPY . /app/

# Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Instalar Tesseract y sus dependencias
RUN apt-get update && \
    apt-get install -y tesseract-ocr && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Exponer el puerto 8000 (este es el puerto en el que Uvicorn escuchará internamente)
EXPOSE 8000

# Configurar el comando de inicio
CMD ["python", "ini_dataextractor.py"]
