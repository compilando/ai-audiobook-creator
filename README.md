# 🎧 AI Audiobook Creator

Sistema inteligente que genera audiobooks completos a partir de un tema utilizando un sistema multiagente basado en LangGraph. Combina generación de contenido con IA con funcionalidades avanzadas de TTS.

## 🌟 Características Principales

### Sistema Multiagente
- **Agente Planificador**: Crea estructura de capítulos
- **Agentes Generadores**: Dos agentes trabajan en paralelo
- **Agente Evaluador**: Evalúa calidad y proporciona feedback iterativo

### Procesamiento de Audio Avanzado
- **Preprocesamiento TTS**: Optimiza texto para síntesis de voz
- **Separación Diálogo/Narración**: Voces diferentes para diálogos y narración
- **Voice Mapping**: Sistema de mapeo de voces por género/personaje
- **Detección de Capítulos**: Detecta automáticamente encabezados
- **Sistema de Reintentos**: Generación robusta con backoff exponencial

### Interfaz de Usuario
- **Editor de Texto Integrado**: Edita contenido antes de generar audio
- **Detección de Estructura**: Visualiza capítulos detectados
- **Estimación de Duración**: Calcula tiempo de audio aproximado

## 📋 Requisitos

- Python 3.10+
- Servidor LLM con API OpenAI-compatible (Ollama, vLLM, LM Studio)
- Servicio TTS (Kokoro o Orpheus)

## 🚀 Instalación Rápida

### Docker Compose (Recomendado)

```bash
# Configurar
cp env.example .env

# Iniciar servicios
docker-compose up -d

# Configurar modelo LLM
./scripts/setup-ollama.sh qwen2.5:7b

# Acceder a la UI
open http://localhost:7860
```

### Instalación Local

```bash
# Entorno virtual
python -m venv venv && source venv/bin/activate

# Dependencias
pip install -r requirements.txt

# Configurar
cp env.example .env

# Ejecutar
python app.py
```

## 🎮 Uso

### Interfaz Web

La UI tiene 3 pestañas:

1. **📝 Generar desde Tema**
   - Ingresa tema del audiobook
   - Selecciona idioma, voz, formato
   - Sistema multiagente genera contenido y audio

2. **✏️ Editor de Texto**
   - Edita texto generado o pega tu propio texto
   - Preprocesa para TTS
   - Detecta capítulos
   - Genera audio desde editor

3. **❓ Ayuda**
   - Documentación de uso

### Uso Programático

```python
# Preprocesamiento de texto
from utils.text_preprocessing import preprocess_full_text, split_and_annotate_text

text = 'El dijo: "Hola mundo"'
processed = preprocess_full_text(text)
parts = split_and_annotate_text(text)  # → [narración, diálogo]

# Voice mapping
from utils.voice_mapping import get_narrator_and_dialogue_voices

voices = get_narrator_and_dialogue_voices('kokoro', 'female')
# → ('af_heart', 'af_sky')

# Detección de capítulos
from utils.audio_utils import detect_chapters_in_text, check_if_chapter_heading

chapters = detect_chapters_in_text(text)
is_chapter = check_if_chapter_heading('Capítulo 1')  # → True
```

## 🔧 Módulos de Utilidades

### `utils/text_preprocessing.py`
| Función                          | Descripción                                |
| -------------------------------- | ------------------------------------------ |
| `preprocess_full_text()`         | Pipeline completo de preprocesamiento      |
| `split_and_annotate_text()`      | Separa diálogo de narración                |
| `normalize_unicode_characters()` | Normaliza comillas y caracteres especiales |
| `fix_unterminated_quotes()`      | Arregla comillas sin cerrar                |

### `utils/voice_mapping.py`
| Función                              | Descripción                          |
| ------------------------------------ | ------------------------------------ |
| `get_narrator_and_dialogue_voices()` | Obtiene voces para narrador/diálogo  |
| `get_voice_for_character_score()`    | Voz basada en score de género (0-10) |
| `load_voice_mappings()`              | Carga configuración desde JSON       |
| `validate_voice()`                   | Valida voz para motor TTS            |

### `utils/audio_utils.py`
| Función                             | Descripción                           |
| ----------------------------------- | ------------------------------------- |
| `generate_audio_with_retry()`       | Generación con reintentos y backoff   |
| `generate_line_audio_with_voices()` | Audio con voces separadas             |
| `detect_chapters_in_text()`         | Detecta todos los capítulos           |
| `check_if_chapter_heading()`        | Verifica si es encabezado de capítulo |
| `estimate_audio_duration()`         | Estima duración en minutos            |

## 📁 Estructura del Proyecto

```
ai-audiobook-creator/
├── agents/                     # Agentes del sistema multiagente
│   ├── planner_agent.py        # Planificador de estructura
│   ├── content_generator_agent.py  # Generador de contenido
│   └── evaluator_agent.py      # Evaluador de calidad
├── workflows/
│   └── content_generation_workflow.py  # Workflow LangGraph
├── integration/
│   ├── content_formatter.py    # Formateador de contenido
│   └── audiobook_adapter.py    # Adaptador con preprocesamiento
├── utils/
│   ├── text_preprocessing.py   # Preprocesamiento TTS
│   ├── voice_mapping.py        # Mapeo de voces
│   ├── audio_utils.py          # Utilidades de audio
│   ├── llm_client.py           # Cliente LLM
│   └── language_support.py     # Soporte multilenguaje
├── static_files/
│   └── voice_map.json          # Configuración voces Kokoro/Orpheus
├── app.py                      # UI Gradio
├── docker-compose.yml          # Configuración Docker
└── requirements.txt
```

## ⚙️ Configuración

### Variables de Entorno (`.env`)

```env
# LLM
LLM_BASE_URL=http://localhost:1234/v1
LLM_MODEL_NAME=Qwen/Qwen3-30B-A3B-Instruct-2507

# TTS
TTS_BASE_URL=http://localhost:8880/v1
TTS_MODEL=kokoro  # o orpheus

# Workflow
MAX_ITERATIONS=3
QUALITY_THRESHOLD=70.0
DEFAULT_LANGUAGE=es
```

### Configuración de Voces (`static_files/voice_map.json`)

```json
{
  "kokoro": {
    "male_narrator": "am_puck",
    "male_dialogue": "af_alloy+am_puck",
    "female_narrator": "af_heart",
    "female_dialogue": "af_sky",
    "male_score_map": { "0": "am_puck", "5": "af_alloy+am_puck", "10": "af_bella" },
    "female_score_map": { "0": "af_heart", "5": "af_alloy+am_puck", "10": "af_bella" }
  }
}
```

## 🎤 Motores TTS Soportados

| Motor       | Características                                                |
| ----------- | -------------------------------------------------------------- |
| **Kokoro**  | Motor por defecto, buena calidad, múltiples voces              |
| **Orpheus** | Alta calidad, soporta etiquetas de emoción (laugh, sigh, gasp) |

## 🌍 Idiomas Soportados

- **Español (es)**: Completamente implementado
- **Inglés (en)**: Completamente implementado

## 🐛 Solución de Problemas

| Error                    | Solución                                                |
| ------------------------ | ------------------------------------------------------- |
| "LLM no disponible"      | Verificar servidor LLM corriendo                        |
| "TTS no disponible"      | Verificar servicio TTS corriendo                        |
| "No hay plan disponible" | Verificar configuración del planificador                |
| Contenido no mejora      | Aumentar `MAX_ITERATIONS` o reducir `QUALITY_THRESHOLD` |

---

**¡Genera audiobooks con IA!** 🎧✨
