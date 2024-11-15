# En VS Code, crea nuevo archivo Dockerfile (sin extensión)
FROM python:3.11-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    zbar-tools \
    libzbar0 \
    libzbar-dev \
    && rm -rf /var/lib/apt/lists/*

# Configurar directorio de trabajo
WORKDIR /app

# Copiar requirements.txt
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Comando para ejecutar la aplicación
CMD uvicorn ini_dataextractor:app --host 0.0.0.0 --port $PORT