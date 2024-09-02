# Usar una imagen base de Python 3.9 ligera
FROM python:3.9-slim

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar el archivo requirements.txt a la imagen
COPY requirements.txt .

# Instalar las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación en la imagen
COPY . .

# Exponer el puerto 5000 (el puerto en el que correrá la aplicación Flask)
EXPOSE 5000

# Comando por defecto para ejecutar la aplicación (permite pasar parámetros)
CMD ["python", "run.py"]

RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*
