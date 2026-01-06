FROM python:3.11-slim

# Metadatos
LABEL maintainer="AI Audiobook Creator"
LABEL description="Sistema multiagente para generación de audiobooks desde temas"

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    curl \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos de requisitos
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Crear directorios necesarios
RUN mkdir -p generated_audiobooks temp_audio audio_samples

# Exponer puerto de Gradio
EXPOSE 7860

# Comando por defecto
CMD ["python", "app.py"]
