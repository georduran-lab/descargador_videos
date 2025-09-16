# Imagen base con Python
FROM python:3.11-slim

# Instalar dependencias del sistema (incluye ffmpeg)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Crear directorio de la app
WORKDIR /app

# Copiar requirements.txt e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Exponer puerto (Koyeb usa variable $PORT automáticamente)
EXPOSE 5000

# Comando de inicio (usar gunicorn en producción)
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--workers", "4"]
