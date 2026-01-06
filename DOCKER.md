# 🐳 Guía de Docker para AI Audiobook Creator

Esta guía explica cómo usar Docker Compose para ejecutar el sistema completo con todos los servicios necesarios.

## 📋 Requisitos Previos

### Software Necesario

1. **Docker**: Versión 20.10 o superior
   ```bash
   docker --version
   ```

2. **Docker Compose**: Versión 2.0 o superior
   ```bash
   docker-compose --version
   ```

3. **NVIDIA Container Toolkit** (para GPU):
   ```bash
   # Verificar instalación
   nvidia-container-toolkit --version
   ```

### Hardware Recomendado

- **CPU**: 8+ cores
- **RAM**: 32GB+ (mínimo 16GB)
- **GPU**: NVIDIA con 8GB+ VRAM (opcional pero recomendado)
- **Disco**: 100GB+ espacio libre (para modelos)

## 🚀 Inicio Rápido

### 1. Configurar Variables de Entorno

```bash
cp env.example .env
```

Edita `.env` si necesitas cambiar configuraciones (la mayoría tienen valores por defecto).

### 2. Iniciar Servicios

```bash
docker-compose up -d
```

Esto iniciará:
- **Ollama** (LLM) en puerto 11434
- **Kokoro TTS** en puerto 8880
- **AI Audiobook Creator** (aplicación principal) en puerto 7860

### 3. Configurar Ollama

Después de iniciar, descarga un modelo:

```bash
./scripts/setup-ollama.sh qwen2.5:7b
```

Modelos recomendados:
- `qwen2.5:7b` - Balance perfecto calidad/velocidad
- `llama3.1:8b` - Muy buena calidad
- `mistral:7b` - Rápido y eficiente
- `gemma:7b` - Ligero y rápido

### 4. Acceder a la UI

Abre tu navegador en:
```
http://localhost:7860
```

## 📝 Comandos Útiles

### Scripts de Ayuda

Usa el script de ayuda para comandos comunes:

```bash
# Iniciar servicios
./scripts/docker-help.sh start

# Ver logs
./scripts/docker-help.sh logs

# Ver logs de un servicio específico
./scripts/docker-help.sh logs ollama

# Ver estado
./scripts/docker-help.sh status

# Detener servicios
./scripts/docker-help.sh stop

# Reiniciar servicios
./scripts/docker-help.sh restart

# Limpiar todo (contenedores, volúmenes, redes)
./scripts/docker-help.sh clean

# Reconstruir imagen
./scripts/docker-help.sh rebuild

# Abrir shell en contenedor
./scripts/docker-help.sh shell
```

### Comandos Docker Compose Directos

```bash
# Ver logs en tiempo real
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f ollama

# Ver estado de servicios
docker-compose ps

# Detener servicios
docker-compose down

# Detener y eliminar volúmenes
docker-compose down -v

# Reconstruir imagen
docker-compose build --no-cache ai_audiobook_creator

# Reiniciar un servicio específico
docker-compose restart ollama
```

## 🔧 Configuración Avanzada

### Cambiar Modelo de Ollama

1. Edita `docker-compose.yml`:
   ```yaml
   environment:
     - LLM_MODEL_NAME=qwen2.5:7b  # Cambia aquí
   ```

2. O edita `.env`:
   ```env
   LLM_MODEL_NAME=llama3.1:8b
   ```

3. Reinicia el servicio:
   ```bash
   docker-compose restart ai_audiobook_creator
   ```

### Usar vLLM en lugar de Ollama

1. Edita `docker-compose.yml` y descomenta la sección de vLLM
2. Comenta o elimina la sección de Ollama
3. Actualiza las variables de entorno:
   ```yaml
   environment:
     - LLM_BASE_URL=http://vllm:8000/v1
   ```

### Usar Orpheus en lugar de Kokoro

1. Edita `docker-compose.yml` y descomenta la sección de Orpheus
2. Comenta o elimina la sección de Kokoro
3. Actualiza las variables de entorno:
   ```yaml
   environment:
     - TTS_BASE_URL=http://orpheus_tts:8880/v1
     - TTS_MODEL=orpheus
   ```

### Configuración para CPU (sin GPU)

1. Cambia la imagen de Kokoro:
   ```yaml
   kokoro_tts:
     image: ghcr.io/remsky/kokoro-fastapi-cpu:v0.2.1
     # Elimina la sección deploy.resources.reservations
   ```

2. Para Ollama, funciona en CPU pero será más lento

### Ajustar Recursos

Edita `docker-compose.yml` para limitar recursos:

```yaml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 16G
    reservations:
      cpus: '2'
      memory: 8G
```

## 🐛 Solución de Problemas

### Los servicios no inician

1. Verifica que Docker está corriendo:
   ```bash
   docker ps
   ```

2. Verifica logs:
   ```bash
   docker-compose logs
   ```

3. Verifica que los puertos no están en uso:
   ```bash
   # Linux/Mac
   lsof -i :7860
   lsof -i :11434
   lsof -i :8880
   ```

### Ollama no descarga modelos

1. Verifica que el contenedor está corriendo:
   ```bash
   docker ps | grep ollama
   ```

2. Intenta descargar manualmente:
   ```bash
   docker exec -it ai_audiobook_ollama ollama pull qwen2.5:7b
   ```

3. Verifica espacio en disco:
   ```bash
   df -h
   ```

### GPU no funciona

1. Verifica que NVIDIA Container Toolkit está instalado:
   ```bash
   nvidia-container-toolkit --version
   ```

2. Verifica que Docker puede acceder a GPU:
   ```bash
   docker run --rm --gpus all nvidia/cuda:11.0.3-base-ubuntu20.04 nvidia-smi
   ```

3. Verifica que el driver NVIDIA está instalado:
   ```bash
   nvidia-smi
   ```

### TTS no responde

1. Verifica que el servicio está corriendo:
   ```bash
   docker-compose ps kokoro_tts
   ```

2. Verifica logs:
   ```bash
   docker-compose logs kokoro_tts
   ```

3. Prueba el endpoint de health:
   ```bash
   curl http://localhost:8880/health
   ```

### La aplicación no se conecta a los servicios

1. Verifica que todos los servicios están en la misma red:
   ```bash
   docker network inspect ai_audiobook_network
   ```

2. Verifica las URLs en las variables de entorno:
   ```bash
   docker-compose exec ai_audiobook_creator env | grep -E "(LLM|TTS)_BASE_URL"
   ```

3. Prueba la conectividad desde el contenedor:
   ```bash
   docker-compose exec ai_audiobook_creator curl http://ollama:11434/api/tags
   ```

## 📊 Monitoreo

### Ver uso de recursos

```bash
# Uso de CPU y memoria
docker stats

# Uso de GPU (si está disponible)
nvidia-smi
```

### Ver logs en tiempo real

```bash
# Todos los servicios
docker-compose logs -f

# Servicio específico
docker-compose logs -f ai_audiobook_creator
```

## 🧹 Limpieza

### Limpiar contenedores y volúmenes

```bash
# Detener y eliminar contenedores, volúmenes y redes
docker-compose down -v

# Limpiar imágenes no usadas
docker image prune -a

# Limpiar todo (¡cuidado!)
docker system prune -a --volumes
```

### Mantener datos pero limpiar contenedores

```bash
# Solo detener contenedores (mantiene volúmenes)
docker-compose down
```

## 📦 Volúmenes

Los volúmenes creados son:

- `ollama_models`: Modelos descargados de Ollama
- `generated_audiobooks`: Audiobooks generados
- `temp_audio`: Archivos temporales de audio
- `audio_samples`: Muestras de audio

Para ver volúmenes:
```bash
docker volume ls | grep ai_audiobook
```

Para inspeccionar un volumen:
```bash
docker volume inspect ai_audiobook_ollama_models
```

## 🔐 Seguridad

### Buenas Prácticas

1. **No exponer servicios a internet** sin autenticación
2. **Usar redes Docker internas** para comunicación entre servicios
3. **Limitar recursos** para evitar DoS
4. **Mantener imágenes actualizadas**:
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

### Variables Sensibles

Nunca commitees el archivo `.env` con credenciales reales. Usa `env.example` como plantilla.

## 📚 Recursos Adicionales

- [Documentación de Docker](https://docs.docker.com/)
- [Documentación de Docker Compose](https://docs.docker.com/compose/)
- [Ollama Documentation](https://ollama.ai/docs)
- [Kokoro TTS FastAPI](https://github.com/remsky/Kokoro-FastAPI)
- [Orpheus TTS FastAPI](https://github.com/prakharsr/Orpheus-TTS-FastAPI)

---

**Última actualización**: Enero 2025
