#web: uvicorn ini_dataextractor:app --host 0.0.0.0 --port $PORT

# Usa una imagen base de Python
FROM python:3.11-slim

# Instala dependencias del sistema para Tesseract y otras librerías necesarias
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    tesseract-ocr-spa \
    build-essential \
    python3-dev \
    && apt-get clean

# Establece el directorio de trabajo
WORKDIR /app

# Copia el archivo de requisitos e instálalos
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código de la aplicación
COPY . .

# Exponer el puerto
EXPOSE 8000

# Ejecuta la aplicación
CMD ["uvicorn", "ini_dataextractor:app", "--host", "0.0.0.0", "--port", "8000"]
