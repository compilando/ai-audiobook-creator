"""
Aplicación Gradio para generación de audiobooks desde temas usando sistema multiagente.

Incluye funcionalidades mejoradas:
- Editor de texto integrado
- Preprocesamiento de texto para TTS
- Detección automática de capítulos
- Voice mapping avanzado
"""

import os
import asyncio
import gradio as gr
from dotenv import load_dotenv
from workflows.content_generation_workflow import create_content_generation_workflow
from integration.audiobook_adapter import AudiobookAdapter
from integration.content_formatter import ContentFormatter
from agents.agent_state import ContentGenerationState
from utils.language_support import LanguageSupport, Language, AudiobookSize
from utils.text_preprocessing import preprocess_full_text, normalize_unicode_characters
from utils.audio_utils import detect_chapters_in_text, estimate_audio_duration
from utils.rich_logger import get_logger, setup_logging, add_log_callback, remove_log_callback, clear_log_buffer, clear_log_callbacks
from utils.voice_mapping import get_voice_choices_for_gradio, get_default_voice_for_language

load_dotenv()

# Inicializar el sistema de logging
logger = setup_logging(os.environ.get("LOG_LEVEL", "INFO"))

# Configuración por defecto
DEFAULT_LANGUAGE = os.environ.get("DEFAULT_LANGUAGE", "es")
MAX_ITERATIONS = int(os.environ.get("MAX_ITERATIONS", 3))
QUALITY_THRESHOLD = float(os.environ.get("QUALITY_THRESHOLD", 70.0))
TTS_MODEL = os.environ.get("TTS_MODEL", "kokoro").lower()


def extract_text_from_content(content) -> str:
    """
    Extrae el texto completo del contenido generado.
    
    El contenido puede ser:
    - Una lista de capítulos (cada uno con 'content')
    - Un diccionario con 'full_text'
    - Un string directo
    
    Args:
        content: El contenido a procesar
        
    Returns:
        El texto completo extraído
    """
    if not content:
        return ""
    
    # Si es una lista de capítulos
    if isinstance(content, list):
        text_parts = []
        for chapter in sorted(content, key=lambda x: x.get("chapter_number", 0) if isinstance(x, dict) else 0):
            if isinstance(chapter, dict):
                chapter_num = chapter.get("chapter_number", "")
                chapter_title = chapter.get("chapter_title", "")
                chapter_content = chapter.get("content", "")
                
                if chapter_num or chapter_title:
                    text_parts.append(f"Capítulo {chapter_num}")
                    if chapter_title:
                        text_parts.append(chapter_title)
                    text_parts.append("")
                
                if chapter_content:
                    text_parts.append(chapter_content)
                    text_parts.append("")
            else:
                text_parts.append(str(chapter))
        
        return "\n".join(text_parts)
    
    # Si es un diccionario con full_text
    if isinstance(content, dict):
        if "full_text" in content:
            return content["full_text"]
        # Intentar extraer contenido de otras formas
        if "content" in content:
            return content["content"]
        return str(content)
    
    # Si es un string directo
    return str(content)


def format_log_for_display(log_entry: dict) -> str:
    """
    Formatea una entrada de log para mostrar en Gradio.
    
    Args:
        log_entry: Entrada de log estructurada
        
    Returns:
        Texto formateado para display
    """
    log_type = log_entry.get("type", "log")
    timestamp = log_entry.get("timestamp", "")
    elapsed = log_entry.get("elapsed", "")
    emoji = log_entry.get("emoji", "")
    level = log_entry.get("level", "INFO")
    message = log_entry.get("message", "")
    
    # Formatear según el tipo
    if log_type == "prompt":
        agent = log_entry.get("agent", "")
        prompt = log_entry.get("prompt", "")[:500]  # Limitar longitud
        return f"\n{'='*50}\n📝 PROMPT [{agent}] [{elapsed}]\n{'='*50}\n{prompt}...\n"
    
    elif log_type == "response":
        agent = log_entry.get("agent", "")
        response = log_entry.get("response", "")[:500]  # Limitar longitud
        word_count = log_entry.get("word_count", 0)
        return f"\n{'='*50}\n💬 RESPUESTA [{agent}] [{elapsed}] ({word_count} palabras)\n{'='*50}\n{response}...\n"
    
    elif log_type == "content":
        chapter = log_entry.get("chapter_number", "")
        title = log_entry.get("chapter_title", "")
        word_count = log_entry.get("word_count", 0)
        return f"📖 Capítulo {chapter}: {title} ({word_count} palabras)\n"
    
    elif log_type == "evaluation":
        score = log_entry.get("score", 0)
        decision = log_entry.get("decision", "")
        strengths = log_entry.get("strengths", [])
        weaknesses = log_entry.get("weaknesses", [])
        
        result = f"\n{'─'*50}\n🔍 EVALUACIÓN: {score}/100 - {decision}\n{'─'*50}\n"
        if strengths:
            result += "✅ Fortalezas:\n"
            for s in strengths[:3]:
                result += f"   • {s}\n"
        if weaknesses:
            result += "⚠️ Áreas de mejora:\n"
            for w in weaknesses[:3]:
                result += f"   • {w}\n"
        return result
    
    elif log_type == "plan":
        plan = log_entry.get("plan", {})
        chapters = plan.get("chapters", [])
        result = f"\n📋 PLAN GENERADO ({len(chapters)} capítulos)\n"
        for ch in chapters[:5]:  # Mostrar máximo 5
            result += f"   • Cap {ch.get('number', '?')}: {ch.get('title', 'Sin título')}\n"
        return result
    
    else:
        # Log normal
        return f"[{elapsed}] {emoji} {message}\n"


def preprocess_text_wrapper(text: str) -> str:
    """
    Preprocesa el texto para TTS.
    
    Args:
        text: El texto a preprocesar
        
    Returns:
        El texto preprocesado
    """
    if not text:
        return ""
    return preprocess_full_text(text)


def detect_chapters_wrapper(text: str) -> str:
    """
    Detecta capítulos en el texto y retorna un resumen.
    
    Args:
        text: El texto a analizar
        
    Returns:
        Resumen de capítulos detectados
    """
    if not text:
        return "No hay texto para analizar."
    
    chapters = detect_chapters_in_text(text)
    
    if not chapters:
        return "No se detectaron capítulos en el texto."
    
    summary = f"📚 Se detectaron {len(chapters)} capítulo(s):\n\n"
    for i, chapter in enumerate(chapters, 1):
        line_count = len([l for l in chapter['lines'] if l.strip()])
        summary += f"  {i}. **{chapter['title']}** - {line_count} líneas\n"
    
    estimated_duration = estimate_audio_duration(text)
    summary += f"\n⏱️ Duración estimada del audio: {estimated_duration:.1f} minutos"
    
    return summary


def find_latest_audiobook(output_format: str) -> str | None:
    """
    Busca el archivo de audiobook más reciente en el directorio generated_audiobooks.
    
    Args:
        output_format: Formato de salida esperado (mp3, m4a, wav, etc.)
        
    Returns:
        Ruta al archivo más reciente o None si no se encuentra
    """
    import glob
    
    audiobooks_dir = "generated_audiobooks"
    if not os.path.exists(audiobooks_dir):
        return None
    
    # Buscar archivos del formato especificado
    pattern = os.path.join(audiobooks_dir, f"*.{output_format}")
    files = glob.glob(pattern)
    
    if not files:
        # Si no hay del formato específico, buscar cualquier formato de audio
        audio_extensions = ["mp3", "m4a", "wav", "m4b", "aac", "opus", "flac"]
        for ext in audio_extensions:
            pattern = os.path.join(audiobooks_dir, f"*.{ext}")
            files.extend(glob.glob(pattern))
    
    if not files:
        return None
    
    # Ordenar por fecha de modificación (más reciente primero)
    files.sort(key=os.path.getmtime, reverse=True)
    
    return files[0] if files else None


def save_edited_text(text: str) -> str:
    """
    Guarda el texto editado en converted_book.txt.
    
    Args:
        text: El texto a guardar
        
    Returns:
        Mensaje de confirmación
    """
    if not text:
        return "❌ No hay texto para guardar."
    
    try:
        with open("converted_book.txt", "w", encoding="utf-8") as f:
            f.write(text)
        return "✅ Texto guardado exitosamente en 'converted_book.txt'"
    except Exception as e:
        return f"❌ Error al guardar: {str(e)}"


def create_slug(text: str, max_length: int = 50) -> str:
    """
    Crea un slug a partir de un texto.
    
    Args:
        text: El texto a convertir en slug
        max_length: Longitud máxima del slug
        
    Returns:
        El slug generado
    """
    import re
    import unicodedata
    
    if not text:
        return "audiobook"
    
    # Normalizar unicode (quitar acentos)
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ASCII', 'ignore').decode('ASCII')
    
    # Convertir a minúsculas
    text = text.lower()
    
    # Reemplazar espacios y caracteres especiales por guiones
    text = re.sub(r'[^a-z0-9]+', '-', text)
    
    # Eliminar guiones al inicio y final
    text = text.strip('-')
    
    # Limitar longitud
    if len(text) > max_length:
        text = text[:max_length].rsplit('-', 1)[0]
    
    return text if text else "audiobook"


def get_voice_options(language: str) -> list:
    """
    Obtiene las opciones de voz para un idioma específico.
    
    Args:
        language: Código de idioma
        
    Returns:
        Lista de opciones para Gradio Dropdown
    """
    return get_voice_choices_for_gradio(TTS_MODEL, language)


def update_voice_options(language: str):
    """
    Actualiza las opciones de voz cuando cambia el idioma.
    
    Args:
        language: Código de idioma
        
    Returns:
        Componente Dropdown actualizado
    """
    choices = get_voice_options(language)
    default_voice = get_default_voice_for_language(TTS_MODEL, language, "male")
    return gr.Dropdown(choices=choices, value=default_voice)


async def generate_audiobook_from_topic(
    topic: str,
    language: str,
    size: str,
    voice_type: str,
    narrator_gender: str,
    voice_id: str,
    output_format: str,
    add_emotion_tags: bool,
    progress=gr.Progress(),
):
    """
    Genera un audiobook completo desde un tema usando el sistema multiagente.
    
    Args:
        topic: Tema del audiobook
        language: Idioma
        size: Tamaño del audiobook ("short", "medium", "long")
        voice_type: Tipo de voz
        narrator_gender: Género del narrador
        voice_id: ID de la voz específica a usar
        output_format: Formato de salida
        add_emotion_tags: Si agregar etiquetas de emoción
        progress: Objeto de progreso de Gradio
        
    Yields:
        Actualizaciones de progreso y resultado final
    """
    if not topic or not topic.strip():
        yield "❌ Por favor, ingresa un tema para el audiobook.", None, ""
        return
    
    # Verificar que el idioma es válido (puede venir como tupla de Gradio)
    if isinstance(language, tuple):
        language = language[1] if len(language) > 1 else language[0]
    
    # Generar slug del tema para el nombre del archivo
    output_filename = create_slug(topic.strip())
    
    try:
        # Obtener logger
        log = get_logger()
        
        # Iniciar workflow con logging
        log.workflow_start("Generación de Audiobook", {
            "tema": topic.strip()[:50] + "..." if len(topic.strip()) > 50 else topic.strip(),
            "idioma": language,
            "formato": output_format,
            "voz": voice_id,
            "tts_model": TTS_MODEL,
            "max_iteraciones": MAX_ITERATIONS,
            "umbral_calidad": QUALITY_THRESHOLD,
            "archivo_salida": output_filename,
        })
        
        # Inicializar workflow
        workflow = create_content_generation_workflow()
        
        # Crear estado inicial
        initial_state: ContentGenerationState = {
            "topic": topic.strip(),
            "language": language,
            "size": size if size else "medium",
            "plan": None,
            "content_v1": None,
            "content_v2": None,
            "evaluation": None,
            "feedback_history": [],
            "iteration_count": 0,
            "max_iterations": MAX_ITERATIONS,
            "quality_threshold": QUALITY_THRESHOLD,
            "final_content": None,
            "metadata": {},
        }
        
        # Ejecutar workflow
        yield "🚀 Iniciando generación de audiobook...\n", None, ""
        yield "📋 Paso 1: Planificando estructura de contenido...\n", None, ""
        
        current_state = initial_state
        step_count = 0
        generated_text = ""
        
        # Procesar estados del workflow usando stream síncrono
        last_state = initial_state.copy()
        plan_shown = False
        content_v1_shown = False
        content_v2_shown = False
        evaluation_shown = False
        final_content_shown = False
        
        try:
            for state_update in workflow.stream(initial_state):
                if isinstance(state_update, dict):
                    for node_name, node_output in state_update.items():
                        if isinstance(node_output, dict):
                            for state_key, state_value in node_output.items():
                                if state_value is not None or last_state.get(state_key) is None:
                                    last_state[state_key] = state_value
                    current_state = last_state
                else:
                    current_state = last_state
                step_count += 1
                
                # Detectar qué paso se completó (mostrar solo una vez cada mensaje)
                if "plan" in current_state and current_state["plan"] and not plan_shown:
                    plan_shown = True
                    num_chapters = len(current_state["plan"].get("chapters", []))
                    yield f"✅ Planificación completada ({num_chapters} capítulo(s))\n✍️ Paso 2: Generando contenido...\n", None, ""
                
                if "content_v1" in current_state and current_state["content_v1"] and not content_v1_shown:
                    content_v1_shown = True
                    yield "✅ Contenido del Generador 1 completado\n", None, ""
                
                if "content_v2" in current_state and current_state["content_v2"] and not content_v2_shown:
                    content_v2_shown = True
                    yield "✅ Contenido del Generador 2 completado\n🔍 Paso 3: Evaluando calidad...\n", None, ""
                
                if "evaluation" in current_state and current_state["evaluation"] and not evaluation_shown:
                    evaluation_shown = True
                    eval_data = current_state["evaluation"]
                    score = eval_data.get("overall_score", 0)
                    decision = eval_data.get("decision", "unknown")
                    yield f"✅ Evaluación: Puntuación {score}/100 - Decisión: {decision}\n", None, ""
                
                if "final_content" in current_state and current_state["final_content"] and not final_content_shown:
                    final_content_shown = True
                    # Extraer el texto del contenido generado (puede ser lista de capítulos)
                    raw_content = current_state["final_content"]
                    generated_text = extract_text_from_content(raw_content)
                    
                    # Aplicar preprocesamiento con el idioma correcto
                    generated_text = preprocess_full_text(generated_text, language)
                    
                    # Mostrar información del contenido
                    word_count = len(generated_text.split()) if generated_text else 0
                    yield f"✅ Contenido fusionado y preprocesado ({word_count} palabras)\n📝 Texto disponible en el editor\n", None, generated_text
        except Exception as workflow_error:
            log.error(f"Error en workflow stream: {type(workflow_error).__name__}: {str(workflow_error)}")
            import traceback
            error_traceback = traceback.format_exc()
            log.error(f"Traceback completo:\n{error_traceback}")
            yield f"❌ Error en el workflow: {type(workflow_error).__name__}: {str(workflow_error)}\n\nDetalles:\n{error_traceback}\n", None, ""
            return
        
        # Verificar que tenemos contenido final
        final_state = last_state
        if not final_state.get("final_content"):
            yield "❌ Error: No se generó contenido final.\n", None, ""
            return
        
        # Guardar el texto preprocesado
        save_edited_text(generated_text)
        
        yield "🎧 Paso 4: Generando audio...\n", None, generated_text
        
        # Generar audiobook usando el adaptador
        formatter = ContentFormatter()
        # Asegurar que final_content no es None
        final_content = final_state.get("final_content") or []
        text_file = formatter.format_to_audiobook_text(final_content, language=language)
        
        adapter = AudiobookAdapter()
        
        output_path = None
        async for progress_update in adapter.generate_audiobook(
            text_file_path=text_file,
            output_format=output_format.lower(),
            voice_type=voice_type,
            narrator_gender=narrator_gender,
            language=language,
            add_emotion_tags=add_emotion_tags,
        ):
            yield f"{progress_update}\n", None, generated_text
            # Intentar extraer la ruta del archivo desde el mensaje
            if "exitosamente:" in progress_update.lower() or "successfully:" in progress_update.lower():
                # Extraer la ruta del mensaje (formato: "... exitosamente: /path/to/file")
                import re
                path_match = re.search(r'(?:exitosamente|successfully)[:\s]+([^\s]+\.(?:mp3|m4a|wav|m4b|aac|opus|flac))', progress_update, re.IGNORECASE)
                if path_match:
                    output_path = path_match.group(1)
            # Fallback: buscar el archivo más reciente si no se extrajo la ruta
            if not output_path and ("successfully" in progress_update.lower() or "created" in progress_update.lower() or "exitosamente" in progress_update.lower()):
                # Buscar archivo más reciente en generated_audiobooks
                output_path = find_latest_audiobook(output_format.lower())
        
        # Si aún no tenemos ruta, buscar el archivo más reciente
        if not output_path:
            output_path = find_latest_audiobook(output_format.lower())
        
        if output_path and os.path.exists(output_path):
            # Renombrar archivo al slug del tema
            import shutil
            final_filename = f"{output_filename}.{output_format.lower()}"
            final_path = os.path.join("generated_audiobooks", final_filename)
            
            # Si el archivo destino ya existe, añadir un sufijo
            if os.path.exists(final_path) and final_path != output_path:
                import time
                timestamp = int(time.time())
                final_filename = f"{output_filename}_{timestamp}.{output_format.lower()}"
                final_path = os.path.join("generated_audiobooks", final_filename)
            
            # Renombrar si es diferente al nombre actual
            if output_path != final_path:
                shutil.move(output_path, final_path)
                output_path = final_path
                log.info(f"Archivo renombrado a: {final_path}")
            
            # Obtener tamaño del archivo
            file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
            log.workflow_complete(True, f"Archivo: {output_path} ({file_size_mb:.2f} MB)")
            yield f"\n🎉 ¡Audiobook generado exitosamente!\n📁 Archivo: {output_path}\n", output_path, generated_text
        else:
            log.workflow_complete(False, "No se encontró el archivo de salida")
            yield "⚠️ El audiobook se generó pero no se encontró el archivo de salida.\n", None, generated_text
            
    except Exception as e:
        log = get_logger()
        log.error(f"Error en generación: {str(e)}")
        log.workflow_complete(False, f"Error: {str(e)}")
        yield f"❌ Error: {str(e)}\n", None, ""
        import traceback
        traceback.print_exc()


async def generate_from_text(
    text: str,
    language: str,
    voice_type: str,
    narrator_gender: str,
    output_format: str,
    add_emotion_tags: bool,
):
    """
    Genera un audiobook directamente desde texto editado.
    
    Args:
        text: El texto a convertir en audio
        language: Idioma
        voice_type: Tipo de voz
        narrator_gender: Género del narrador
        output_format: Formato de salida
        add_emotion_tags: Si agregar etiquetas de emoción
        
    Yields:
        Actualizaciones de progreso
    """
    if not text or not text.strip():
        yield "❌ No hay texto para generar audio.", None
        return
    
    try:
        # Preprocesar y guardar el texto (usar idioma seleccionado)
        processed_text = preprocess_full_text(text, language)
        save_result = save_edited_text(processed_text)
        yield f"{save_result}\n", None
        
        # Generar audiobook
        yield "🎧 Iniciando generación de audio...\n", None
        
        adapter = AudiobookAdapter()
        
        output_path = None
        async for progress_update in adapter.generate_audiobook(
            text_file_path="converted_book.txt",
            output_format=output_format.lower(),
            voice_type=voice_type,
            narrator_gender=narrator_gender,
            language=language,
            add_emotion_tags=add_emotion_tags,
        ):
            yield f"{progress_update}\n", None
            # Intentar extraer la ruta del archivo desde el mensaje
            if "exitosamente:" in progress_update.lower() or "successfully:" in progress_update.lower():
                import re
                path_match = re.search(r'(?:exitosamente|successfully)[:\s]+([^\s]+\.(?:mp3|m4a|wav|m4b|aac|opus|flac))', progress_update, re.IGNORECASE)
                if path_match:
                    output_path = path_match.group(1)
            # Fallback: buscar el archivo más reciente
            if not output_path and ("successfully" in progress_update.lower() or "created" in progress_update.lower() or "exitosamente" in progress_update.lower()):
                output_path = find_latest_audiobook(output_format.lower())
        
        # Si aún no tenemos ruta, buscar el archivo más reciente
        if not output_path:
            output_path = find_latest_audiobook(output_format.lower())
        
        if output_path and os.path.exists(output_path):
            file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
            yield f"\n🎉 ¡Audiobook generado exitosamente!\n📁 Archivo: {output_path} ({file_size_mb:.2f} MB)\n", output_path
        else:
            yield "⚠️ El audiobook se generó pero no se encontró el archivo de salida.\n", None
            
    except Exception as e:
        log = get_logger()
        log.error(f"Error en generate_from_text: {type(e).__name__}: {str(e)}")
        import traceback
        error_traceback = traceback.format_exc()
        log.error(f"Traceback:\n{error_traceback}")
        yield f"❌ Error: {type(e).__name__}: {str(e)}\n\nDetalles:\n{error_traceback}\n", None


def create_ui():
    """Crea la interfaz de usuario con Gradio."""
    
    css = """
    .step-heading {font-size: 1.2rem; font-weight: bold; margin-bottom: 0.5rem}
    .editor-container {min-height: 400px}
    """
    
    with gr.Blocks(title="Generador de Audiobooks con IA", theme=gr.themes.Default(), css=css) as app:
        gr.Markdown("# Generador de Audiobooks con Sistema Multiagente")
        gr.Markdown("Genera audiobooks completos desde un tema o edita texto directamente para convertirlo en audio.")
        
        with gr.Tabs():
            # Tab 1: Generación desde Tema
            with gr.Tab("📝 Generar desde Tema"):
                with gr.Row():
                    with gr.Column(scale=2):
                        topic_input = gr.Textbox(
                            label="Tema del Audiobook",
                            placeholder="Ejemplo: Desarrollo Java, Historia de España, Programación Python...",
                            lines=2,
                            info="Describe el tema sobre el cual quieres generar el audiobook",
                        )
                        
                        with gr.Row():
                            language_input = gr.Dropdown(
                                choices=[
                                    (LanguageSupport.get_language_name("es"), "es"),
                                    (LanguageSupport.get_language_name("en"), "en"),
                                ],
                                value=DEFAULT_LANGUAGE,
                                label="🌐 Idioma",
                                info="Idioma del contenido y del audiobook",
                            )
                            
                            size_input = gr.Dropdown(
                                choices=LanguageSupport.get_size_choices(DEFAULT_LANGUAGE),
                                value="medium",
                                label="📏 Tamaño",
                                info="Duración aproximada del audiobook",
                            )
                    
                    with gr.Column(scale=1):
                        voice_type_input = gr.Radio(
                            choices=["Single Voice", "Multi-Voice"],
                            value="Single Voice",
                            label="Tipo de Voz",
                            info="Single Voice: una voz para todo. Multi-Voice: voces diferentes para diálogos",
                        )
                        
                        narrator_gender_input = gr.Radio(
                            choices=["male", "female"],
                            value="male",
                            label="Género del Narrador (solo si no se elige voz específica)",
                        )
                
                with gr.Row():
                    # Selector de voz específica
                    voice_input = gr.Dropdown(
                        choices=get_voice_options(DEFAULT_LANGUAGE),
                        value=get_default_voice_for_language(TTS_MODEL, DEFAULT_LANGUAGE, "male"),
                        label="🎤 Voz del Narrador",
                        info="Selecciona la voz específica para el audiobook",
                    )
                    
                    output_format_input = gr.Dropdown(
                        choices=["MP3", "M4A", "WAV", "AAC", "OPUS", "FLAC", "M4B"],
                        value="MP3",
                        label="Formato de Salida",
                        info="M4B incluye capítulos y portada (requiere calibre)",
                    )
                    
                    emotion_tags_input = gr.Checkbox(
                        value=False,
                        label="Agregar Etiquetas de Emoción",
                        info=f"Solo disponible con Orpheus TTS (actual: {TTS_MODEL})",
                        interactive=(TTS_MODEL == "orpheus"),
                    )
                
                # Actualizar voces cuando cambia el idioma
                language_input.change(
                    fn=update_voice_options,
                    inputs=[language_input],
                    outputs=[voice_input],
                )
                
                generate_btn = gr.Button("🚀 Generar Audiobook", variant="primary", size="lg")
                
                with gr.Row():
                    with gr.Column():
                        progress_output = gr.Textbox(
                            label="Progreso",
                            lines=10,
                            interactive=False,
                            placeholder="El progreso de generación aparecerá aquí...",
                        )
                    
                    with gr.Column():
                        audiobook_file = gr.File(
                            label="Audiobook Generado",
                            interactive=False,
                        )
            
            # Tab 2: Editor de Texto
            with gr.Tab("✏️ Editor de Texto"):
                gr.Markdown('<div class="step-heading">📖 Editor de Contenido</div>')
                gr.Markdown("Edita el texto generado antes de convertirlo en audio, o pega tu propio texto.")
                
                with gr.Row():
                    with gr.Column(scale=3):
                        # Botones de navegación
                        with gr.Row():
                            preprocess_btn = gr.Button("🔧 Preprocesar Texto", size="sm")
                            detect_chapters_btn = gr.Button("📚 Detectar Capítulos", size="sm")
                            save_btn = gr.Button("💾 Guardar Texto", size="sm", variant="primary")
                        
                        text_editor = gr.Textbox(
                            label="Editor de Texto",
                            placeholder="El texto generado aparecerá aquí para edición, o pega tu propio texto...",
                            lines=20,
                            max_lines=50,
                            interactive=True,
                            elem_classes=["editor-container"],
                        )
                    
                    with gr.Column(scale=1):
                        chapter_info = gr.Markdown(
                            value="📊 Información de capítulos aparecerá aquí después de detectarlos.",
                        )
                        
                        save_status = gr.Textbox(
                            label="Estado",
                            lines=2,
                            interactive=False,
                        )
                
                gr.Markdown("---")
                gr.Markdown("### 🎧 Generar Audio desde Texto Editado")
                
                with gr.Row():
                    editor_language = gr.Dropdown(
                        choices=[
                            (LanguageSupport.get_language_name("es"), "es"),
                            (LanguageSupport.get_language_name("en"), "en"),
                        ],
                        value=DEFAULT_LANGUAGE,
                        label="Idioma",
                    )
                    
                    editor_voice_type = gr.Radio(
                        choices=["Single Voice", "Multi-Voice"],
                        value="Single Voice",
                        label="Tipo de Voz",
                    )
                    
                    editor_narrator_gender = gr.Radio(
                        choices=["male", "female"],
                        value="female",
                        label="Género del Narrador",
                    )
                
                with gr.Row():
                    editor_output_format = gr.Dropdown(
                        choices=["MP3", "M4A", "WAV", "AAC", "OPUS", "FLAC", "M4B"],
                        value="MP3",
                        label="Formato de Salida",
                    )
                    
                    editor_emotion_tags = gr.Checkbox(
                        value=False,
                        label="Etiquetas de Emoción",
                        interactive=(TTS_MODEL == "orpheus"),
                    )
                
                generate_from_text_btn = gr.Button("🎧 Generar Audio desde Texto", variant="primary", size="lg")
                
                with gr.Row():
                    editor_progress = gr.Textbox(
                        label="Progreso de Generación",
                        lines=8,
                        interactive=False,
                    )
                    
                    editor_audiobook_file = gr.File(
                        label="Audiobook Generado",
                        interactive=False,
                    )
            
            # Tab 3: Logs Detallados
            with gr.Tab("📊 Logs Detallados"):
                gr.Markdown("### 🔍 Visor de Logs en Tiempo Real")
                gr.Markdown("Aquí puedes ver los logs detallados incluyendo prompts, respuestas y evaluaciones.")
                
                with gr.Row():
                    refresh_logs_btn = gr.Button("🔄 Actualizar Logs", size="sm")
                    clear_logs_btn = gr.Button("🗑️ Limpiar Logs", size="sm", variant="secondary")
                
                with gr.Row():
                    with gr.Column(scale=2):
                        detailed_logs = gr.Textbox(
                            label="📋 Logs del Sistema",
                            lines=25,
                            max_lines=50,
                            interactive=False,
                            placeholder="Los logs detallados aparecerán aquí durante la generación...",
                        )
                    
                    with gr.Column(scale=1):
                        gr.Markdown("#### 📈 Estadísticas")
                        stats_display = gr.Markdown(
                            value="Ejecuta una generación para ver estadísticas."
                        )
                
                def get_formatted_logs():
                    """Obtiene y formatea los logs acumulados."""
                    from utils.rich_logger import get_log_buffer
                    buffer = get_log_buffer()
                    
                    if not buffer:
                        return "No hay logs disponibles aún.\n\nInicia una generación para ver los logs.", "Sin estadísticas"
                    
                    # Formatear logs
                    formatted_lines = []
                    stats = {
                        "prompts": 0,
                        "responses": 0,
                        "evaluations": 0,
                        "errors": 0,
                        "total_words": 0,
                    }
                    
                    for entry in buffer:
                        log_type = entry.get("type", "log")
                        
                        if log_type == "prompt":
                            stats["prompts"] += 1
                            agent = entry.get("agent", "")
                            prompt = entry.get("prompt", "")
                            system = entry.get("system_prompt", "")
                            formatted_lines.append(f"\n{'='*60}")
                            formatted_lines.append(f"📝 PROMPT [{agent}]")
                            formatted_lines.append(f"{'='*60}")
                            if system:
                                formatted_lines.append(f"🔧 System: {system[:200]}...")
                            formatted_lines.append(f"\n{prompt[:1000]}...")
                            formatted_lines.append("")
                        
                        elif log_type == "response":
                            stats["responses"] += 1
                            agent = entry.get("agent", "")
                            response = entry.get("response", "")
                            word_count = entry.get("word_count", 0)
                            stats["total_words"] += word_count
                            formatted_lines.append(f"\n{'='*60}")
                            formatted_lines.append(f"💬 RESPUESTA [{agent}] ({word_count} palabras)")
                            formatted_lines.append(f"{'='*60}")
                            formatted_lines.append(f"\n{response[:1000]}...")
                            formatted_lines.append("")
                        
                        elif log_type == "evaluation":
                            stats["evaluations"] += 1
                            score = entry.get("score", 0)
                            decision = entry.get("decision", "")
                            strengths = entry.get("strengths", [])
                            weaknesses = entry.get("weaknesses", [])
                            formatted_lines.append(f"\n{'─'*60}")
                            formatted_lines.append(f"🔍 EVALUACIÓN: {score}/100 - {decision}")
                            formatted_lines.append(f"{'─'*60}")
                            if strengths:
                                formatted_lines.append("✅ Fortalezas:")
                                for s in strengths[:5]:
                                    formatted_lines.append(f"   • {s}")
                            if weaknesses:
                                formatted_lines.append("⚠️ Áreas de mejora:")
                                for w in weaknesses[:5]:
                                    formatted_lines.append(f"   • {w}")
                            formatted_lines.append("")
                        
                        elif log_type == "plan":
                            plan = entry.get("plan", {})
                            chapters = plan.get("chapters", [])
                            formatted_lines.append(f"\n📋 PLAN GENERADO ({len(chapters)} capítulos)")
                            for ch in chapters:
                                formatted_lines.append(f"   • Cap {ch.get('number', '?')}: {ch.get('title', 'Sin título')}")
                            formatted_lines.append("")
                        
                        elif log_type == "content":
                            chapter = entry.get("chapter_number", "")
                            title = entry.get("chapter_title", "")
                            word_count = entry.get("word_count", 0)
                            formatted_lines.append(f"📖 Capítulo {chapter}: {title} ({word_count} palabras)")
                        
                        elif log_type == "log":
                            level = entry.get("level", "INFO")
                            if level == "ERROR":
                                stats["errors"] += 1
                            elapsed = entry.get("elapsed", "")
                            emoji = entry.get("emoji", "")
                            message = entry.get("message", "")
                            formatted_lines.append(f"[{elapsed}] {emoji} {message}")
                    
                    # Generar estadísticas
                    stats_text = f"""
**📊 Resumen de Actividad**
                    
- 📝 Prompts enviados: {stats['prompts']}
- 💬 Respuestas recibidas: {stats['responses']}
- 🔍 Evaluaciones: {stats['evaluations']}
- ❌ Errores: {stats['errors']}
- 📖 Palabras totales: {stats['total_words']:,}

**📋 Total de logs: {len(buffer)}**
"""
                    
                    return "\n".join(formatted_lines), stats_text
                
                def clear_all_logs():
                    """Limpia todos los logs."""
                    clear_log_buffer()
                    return "Logs limpiados.\n\nInicia una nueva generación para ver logs.", "Sin estadísticas"
                
                # Event handlers para logs
                refresh_logs_btn.click(
                    fn=get_formatted_logs,
                    inputs=[],
                    outputs=[detailed_logs, stats_display],
                )
                
                clear_logs_btn.click(
                    fn=clear_all_logs,
                    inputs=[],
                    outputs=[detailed_logs, stats_display],
                )
            
            # Tab 4: Ayuda
            with gr.Tab("❓ Ayuda"):
                gr.Markdown("""
                ## 📖 Cómo usar
                
                ### Opción 1: Generar desde Tema
                1. **Ingresa un tema**: Describe el tema sobre el cual quieres generar el audiobook
                2. **Selecciona configuración**: Idioma, tipo de voz, formato, etc.
                3. **Genera**: El sistema multiagente:
                   - Planificará la estructura del contenido
                   - Generará contenido con agentes independientes
                   - Evaluará la calidad y mejorará iterativamente
                   - Generará el audio final
                
                ### Opción 2: Editor de Texto
                1. **Genera contenido** desde la primera pestaña, o **pega tu propio texto**
                2. **Edita** el texto según necesites
                3. **Preprocesa** el texto para optimizarlo para TTS
                4. **Detecta capítulos** para ver la estructura
                5. **Genera audio** directamente desde el editor
                
                ## 🔧 Funcionalidades
                
                - **Preprocesamiento de Texto**: Optimiza el texto para TTS (puntuación, comillas, caracteres especiales)
                - **Detección de Capítulos**: Detecta automáticamente encabezados de capítulo
                - **Separación Diálogo/Narración**: Usa voces diferentes para diálogos y narración
                - **Voice Mapping Avanzado**: Mapeo inteligente de voces por género/personaje
                - **Sistema de Reintentos**: Reintentos automáticos para generación de audio robusta
                
                ## ⚙️ Requisitos
                
                - Servidor LLM corriendo (Ollama, vLLM, LM Studio, etc.)
                - Servicio TTS corriendo (Kokoro o Orpheus)
                - Configuración correcta en archivo `.env`
                
                ## 🎤 Motores TTS Soportados
                
                - **Kokoro**: Motor TTS por defecto, buena calidad
                - **Orpheus**: Alta calidad, soporta etiquetas de emoción (laugh, sigh, gasp, etc.)
                """)
        
        # Event handlers - Tab 1
        generate_btn.click(
            fn=generate_audiobook_from_topic,
            inputs=[
                topic_input,
                language_input,
                size_input,
                voice_type_input,
                narrator_gender_input,
                voice_input,
                output_format_input,
                emotion_tags_input,
            ],
            outputs=[progress_output, audiobook_file, text_editor],
        )
        
        # Event handlers - Tab 2 (Editor)
        preprocess_btn.click(
            fn=preprocess_text_wrapper,
            inputs=[text_editor],
            outputs=[text_editor],
        )
        
        detect_chapters_btn.click(
            fn=detect_chapters_wrapper,
            inputs=[text_editor],
            outputs=[chapter_info],
        )
        
        save_btn.click(
            fn=save_edited_text,
            inputs=[text_editor],
            outputs=[save_status],
        )
        
        generate_from_text_btn.click(
            fn=generate_from_text,
            inputs=[
                text_editor,
                editor_language,
                editor_voice_type,
                editor_narrator_gender,
                editor_output_format,
                editor_emotion_tags,
            ],
            outputs=[editor_progress, editor_audiobook_file],
        )
    
    return app


if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI
    
    app = FastAPI()
    gradio_app = create_ui()
    
    app = gr.mount_gradio_app(app, gradio_app, path="/")
    
    port = int(os.environ.get("GRADIO_PORT", 7860))
    host = os.environ.get("GRADIO_HOST", "0.0.0.0")
    
    uvicorn.run(app, host=host, port=port)
