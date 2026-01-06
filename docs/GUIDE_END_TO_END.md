# 🎧 Guía End-to-End: Generación de Audiobooks

Esta guía describe el flujo completo para generar audiobooks con IA, desde la configuración hasta el archivo MP3 final.

## 📋 Índice

1. [Arquitectura del Sistema](#arquitectura-del-sistema)
2. [Opciones de Ejecución](#opciones-de-ejecución)
3. [Flujo End-to-End con Docker](#flujo-end-to-end-con-docker)
4. [Flujo End-to-End sin Docker](#flujo-end-to-end-sin-docker)
5. [Calidad de Voz](#calidad-de-voz)
6. [Tests Unitarios](#tests-unitarios)

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI Audiobook Creator                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   1. ENTRADA                                                    │
│   ┌─────────┐                                                   │
│   │  Tema   │ "Materialismo Filosófico de Gustavo Bueno"       │
│   └────┬────┘                                                   │
│        ▼                                                        │
│   2. PLANIFICACIÓN (LLM)                                        │
│   ┌─────────────────┐                                           │
│   │ Planner Agent   │ → Estructura de capítulos                 │
│   │ (Ollama/LM)     │                                           │
│   └────────┬────────┘                                           │
│            ▼                                                    │
│   3. GENERACIÓN (LLM)                                           │
│   ┌─────────────────┐  ┌─────────────────┐                     │
│   │ Generator 1     │  │ Generator 2     │                     │
│   │ (Paralelo)      │  │ (Paralelo)      │                     │
│   └────────┬────────┘  └────────┬────────┘                     │
│            └──────────┬─────────┘                               │
│                       ▼                                         │
│   4. EVALUACIÓN (LLM)                                           │
│   ┌─────────────────┐                                           │
│   │ Evaluator Agent │ → Score + Feedback                        │
│   │ (Iterativo)     │                                           │
│   └────────┬────────┘                                           │
│            ▼                                                    │
│   5. FORMATEO                                                   │
│   ┌─────────────────┐                                           │
│   │ ContentFormatter│ → Texto optimizado para TTS               │
│   └────────┬────────┘                                           │
│            ▼                                                    │
│   6. SÍNTESIS DE VOZ (TTS)                                      │
│   ┌─────────────────┐                                           │
│   │ Kokoro TTS      │ → Audio de alta calidad                   │
│   │ (o gTTS)        │                                           │
│   └────────┬────────┘                                           │
│            ▼                                                    │
│   7. SALIDA                                                     │
│   ┌─────────────────┐                                           │
│   │ audiobook.mp3   │ ← Archivo final                           │
│   └─────────────────┘                                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Opciones de Ejecución

| Modo                | LLM          | TTS           | Calidad Audio   | Requisitos            |
| ------------------- | ------------ | ------------- | --------------- | --------------------- |
| **Docker Completo** | Ollama (GPU) | Kokoro (GPU)  | ⭐⭐⭐⭐⭐ Alta      | GPU NVIDIA, 16GB+ RAM |
| **Docker CPU**      | Ollama (CPU) | Kokoro (CPU)  | ⭐⭐⭐⭐ Media-Alta | 16GB+ RAM             |
| **Local + gTTS**    | Ninguno      | gTTS (Google) | ⭐⭐⭐ Media       | Solo Internet         |
| **Híbrido**         | Externo      | Kokoro/gTTS   | Variable        | Depende               |

---

## 🐳 Flujo End-to-End con Docker

### Paso 1: Configuración Inicial

```bash
# Clonar el proyecto
cd ai-audiobook-creator

# Copiar configuración
cp env.example .env

# Editar .env si es necesario
nano .env
```

### Paso 2: Iniciar Servicios Docker

```bash
# Iniciar todos los servicios
make docker-up

# O directamente:
docker-compose up -d

# Ver estado
make docker-status
```

**Servicios iniciados:**
- **Ollama** (puerto 11434): LLM para generación de contenido
- **Kokoro TTS** (puerto 8880): Síntesis de voz de alta calidad
- **AI Audiobook Creator** (puerto 7860): Interfaz web

### Paso 3: Descargar Modelo LLM

```bash
# Configurar Ollama con modelo recomendado
make ollama-setup

# O modelo específico:
make ollama-pull MODEL=llama3.1
```

### Paso 4: Verificar Servicios

```bash
make check-services
```

Salida esperada:
```
Verificando servicios...
  LLM (localhost:1234): ✓ OK
  TTS (localhost:8880): ✓ OK
  Ollama (localhost:11434): ✓ OK
```

### Paso 5: Generar Audiobook

**Opción A: Interfaz Web**
```bash
# Abrir en navegador
open http://localhost:7860
```

**Opción B: Línea de comandos**
```bash
# Generar con Makefile
make generate-audio

# O script directo con voz premium:
./venv/bin/python scripts/generate_audiobook_premium.py --voice ef_dora
```

### Paso 6: Reproducir Resultado

```bash
make play-audio

# O directamente:
mpv generated_audiobooks/materialismo_gustavo_bueno.mp3
```

### Paso 7: Detener Servicios

```bash
make docker-down
```

---

## 💻 Flujo End-to-End sin Docker

### Paso 1: Configuración

```bash
# Crear entorno virtual e instalar dependencias
make setup

# O manualmente:
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
pip install gTTS pydub
```

### Paso 2: Generar Audiobook (gTTS)

```bash
# Generar con gTTS (requiere internet)
make generate-audio

# O directamente:
./venv/bin/python scripts/generate_materialismo_audio.py
```

### Paso 3: Reproducir

```bash
mpv generated_audiobooks/materialismo_gustavo_bueno.mp3
```

---

## 🎤 Calidad de Voz

### Comparativa de Motores TTS

| Motor             | Naturalidad | Velocidad | Idiomas | Requisitos      |
| ----------------- | ----------- | --------- | ------- | --------------- |
| **Kokoro TTS**    | ⭐⭐⭐⭐⭐       | Media     | Multi   | GPU recomendada |
| **gTTS (Google)** | ⭐⭐⭐         | Rápida    | Multi   | Solo Internet   |
| **Orpheus TTS**   | ⭐⭐⭐⭐⭐       | Lenta     | EN      | GPU requerida   |

### Voces Recomendadas (Kokoro TTS)

#### Para Español:
| Voz       | Descripción        | Uso Recomendado       |
| --------- | ------------------ | --------------------- |
| `ef_dora` | Femenina española  | Narraciones generales |
| `em_alex` | Masculina española | Contenido académico   |

#### Para Inglés:
| Voz         | Descripción         | Uso Recomendado             |
| ----------- | ------------------- | --------------------------- |
| `af_sky`    | Femenina americana  | Muy natural, conversacional |
| `af_nicole` | Femenina americana  | Clara, profesional          |
| `bf_emma`   | Femenina británica  | Elegante, formal            |
| `am_adam`   | Masculina americana | Profunda, autoritativa      |
| `bm_george` | Masculina británica | Narraciones formales        |

### Cómo Usar Voces Específicas

```bash
# Español con voz femenina
./venv/bin/python scripts/generate_audiobook_premium.py --voice ef_dora --lang es

# Inglés con voz masculina británica
./venv/bin/python scripts/generate_audiobook_premium.py --voice bm_george --lang en
```

### Mejorar Calidad con Docker

1. **Asegúrate de tener GPU NVIDIA** con drivers actualizados
2. **Instala nvidia-container-toolkit**:
   ```bash
   sudo apt install nvidia-container-toolkit
   sudo systemctl restart docker
   ```
3. **Usa la imagen GPU de Kokoro**:
   ```yaml
   # En docker-compose.yml
   kokoro_tts:
     image: ghcr.io/remsky/kokoro-fastapi-gpu:v0.2.1
   ```

---

## 🧪 Tests Unitarios

### ¿Funcionan con Docker?

**Sí**, los tests de integración funcionan cuando Docker está corriendo:

```bash
# Iniciar Docker primero
make docker-up

# Esperar a que los servicios estén listos
sleep 30

# Ejecutar tests de integración
make test-integration
```

### Tests Disponibles

| Comando                 | Descripción            | Requiere Docker      |
| ----------------------- | ---------------------- | -------------------- |
| `make test`             | Todos los tests        | No (unitarios pasan) |
| `make test-unit`        | Solo unitarios         | No                   |
| `make test-integration` | Con servicios externos | Sí                   |
| `make test-audio`       | Genera audio de prueba | No (usa gTTS)        |

### Ejecutar Test de Materialismo

```bash
# Test que genera contenido sobre Gustavo Bueno
./venv/bin/python -m pytest tests/test_audiobook_generation.py::TestMaterialismoGustvooBuenoGeneration -v -s
```

**Salida esperada:**
```
tests/test_audiobook_generation.py::TestMaterialismoGustvooBuenoGeneration::test_generate_materialismo_content
============================================================
Archivo generado: /tmp/.../materialismo_gustavo_bueno.txt
Tamaño: 4349 bytes
Líneas: 100
Palabras: 610
============================================================
PASSED
```

---

## 📁 Archivos Generados

```
generated_audiobooks/
├── materialismo_gustavo_bueno.mp3      # Audio (gTTS)
├── materialismo_gustavo_bueno_premium.mp3  # Audio (Kokoro, si disponible)
└── materialismo_gustavo_bueno.txt      # Texto fuente
```

---

## 🚀 Resumen de Comandos

```bash
# Configuración
make setup                  # Configuración inicial
make install-dev            # Dependencias de desarrollo

# Docker
make docker-up              # Iniciar servicios
make docker-down            # Detener servicios
make check-services         # Verificar estado

# Generación
make generate-audio         # Generar audiobook
make play-audio             # Reproducir audiobook

# Tests
make test                   # Ejecutar todos los tests
make test-audio             # Test de generación de audio

# Utilidades
make help                   # Ver todos los comandos
make clean                  # Limpiar cache
```

---

## ❓ Preguntas Frecuentes

### ¿Cómo mejoro la calidad de voz?

1. Usa Docker con Kokoro TTS (GPU)
2. Selecciona la voz apropiada (`ef_dora` para español)
3. Ajusta la velocidad si es necesario

### ¿Funciona sin GPU?

Sí, pero con limitaciones:
- Usa `ghcr.io/remsky/kokoro-fastapi-cpu:v0.2.1`
- O usa gTTS (calidad media pero rápido)

### ¿Puedo usar otros temas?

Sí, modifica el contenido en:
- `scripts/generate_audiobook_premium.py` función `get_materialismo_content()`
- O usa la interfaz web en http://localhost:7860

---

**¡Disfruta creando audiobooks con IA!** 🎧✨
