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
from utils.language_support import LanguageSupport, Language
from utils.text_preprocessing import preprocess_full_text, normalize_unicode_characters
from utils.audio_utils import detect_chapters_in_text, estimate_audio_duration
from utils.rich_logger import get_logger, setup_logging

load_dotenv()

# Inicializar el sistema de logging
logger = setup_logging(os.environ.get("LOG_LEVEL", "INFO"))

# Configuración por defecto
DEFAULT_LANGUAGE = os.environ.get("DEFAULT_LANGUAGE", "es")
MAX_ITERATIONS = int(os.environ.get("MAX_ITERATIONS", 3))
QUALITY_THRESHOLD = float(os.environ.get("QUALITY_THRESHOLD", 70.0))
TTS_MODEL = os.environ.get("TTS_MODEL", "kokoro").lower()


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


async def generate_audiobook_from_topic(
    topic: str,
    language: str,
    voice_type: str,
    narrator_gender: str,
    output_format: str,
    add_emotion_tags: bool,
    progress=gr.Progress(),
):
    """
    Genera un audiobook completo desde un tema usando el sistema multiagente.
    
    Args:
        topic: Tema del audiobook
        language: Idioma
        voice_type: Tipo de voz
        narrator_gender: Género del narrador
        output_format: Formato de salida
        add_emotion_tags: Si agregar etiquetas de emoción
        progress: Objeto de progreso de Gradio
        
    Yields:
        Actualizaciones de progreso y resultado final
    """
    if not topic or not topic.strip():
        yield "❌ Por favor, ingresa un tema para el audiobook.", None, ""
        return
    
    try:
        # Obtener logger
        log = get_logger()
        
        # Iniciar workflow con logging
        log.workflow_start("Generación de Audiobook", {
            "tema": topic.strip()[:50] + "..." if len(topic.strip()) > 50 else topic.strip(),
            "idioma": language,
            "formato": output_format,
            "voz": voice_type,
            "tts_model": TTS_MODEL,
            "max_iteraciones": MAX_ITERATIONS,
            "umbral_calidad": QUALITY_THRESHOLD,
        })
        
        # Inicializar workflow
        workflow = create_content_generation_workflow()
        
        # Crear estado inicial
        initial_state: ContentGenerationState = {
            "topic": topic.strip(),
            "language": language,
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
        try:
            for state_update in workflow.stream(initial_state):
                if isinstance(state_update, dict):
                    for key, value in state_update.items():
                        if isinstance(value, dict) and key in last_state:
                            last_state[key].update(value)
                        else:
                            last_state[key] = value
                    current_state = last_state
                else:
                    current_state = state_update if isinstance(state_update, dict) else last_state
                step_count += 1
                
                # Detectar qué paso se completó
                if "plan" in current_state and current_state["plan"]:
                    yield "✅ Planificación completada\n✍️ Paso 2: Generando contenido...\n", None, ""
                
                if "content_v1" in current_state and current_state["content_v1"]:
                    yield "✅ Contenido del Generador 1 completado\n", None, ""
                
                if "content_v2" in current_state and current_state["content_v2"]:
                    yield "✅ Contenido del Generador 2 completado\n🔍 Paso 3: Evaluando calidad...\n", None, ""
                
                if "evaluation" in current_state and current_state["evaluation"]:
                    eval_data = current_state["evaluation"]
                    score = eval_data.get("overall_score", 0)
                    decision = eval_data.get("decision", "unknown")
                    yield f"✅ Evaluación: Puntuación {score}/100 - Decisión: {decision}\n", None, ""
                
                if "final_content" in current_state and current_state["final_content"]:
                    # Preprocesar el contenido generado
                    raw_content = current_state["final_content"]
                    if isinstance(raw_content, dict):
                        generated_text = raw_content.get("full_text", str(raw_content))
                    else:
                        generated_text = str(raw_content)
                    
                    # Aplicar preprocesamiento
                    generated_text = preprocess_full_text(generated_text)
                    yield "✅ Contenido formateado y preprocesado\n📝 Texto disponible en el editor\n", None, generated_text
                
                last_state = current_state.copy() if isinstance(current_state, dict) else last_state
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
        text_file = formatter.format_to_audiobook_text(final_state["final_content"])
        
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
            if "successfully" in progress_update.lower() or "created" in progress_update.lower():
                if output_format.lower() == "m4b":
                    output_path = "generated_audiobooks/audiobook.m4b"
                else:
                    output_path = f"generated_audiobooks/audiobook.{output_format.lower()}"
        
        if output_path and os.path.exists(output_path):
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
        # Preprocesar y guardar el texto
        processed_text = preprocess_full_text(text)
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
            if "successfully" in progress_update.lower() or "created" in progress_update.lower():
                if output_format.lower() == "m4b":
                    output_path = "generated_audiobooks/audiobook.m4b"
                else:
                    output_path = f"generated_audiobooks/audiobook.{output_format.lower()}"
        
        if output_path and os.path.exists(output_path):
            yield f"\n🎉 ¡Audiobook generado exitosamente!\n📁 Archivo: {output_path}\n", output_path
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
        gr.Markdown("# 🎧 Generador de Audiobooks con Sistema Multiagente")
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
                        
                        language_input = gr.Dropdown(
                            choices=[
                                (LanguageSupport.get_language_name("es"), "es"),
                                (LanguageSupport.get_language_name("en"), "en"),
                            ],
                            value=DEFAULT_LANGUAGE,
                            label="Idioma",
                            info="Idioma del contenido y del audiobook",
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
                            value="female",
                            label="Género del Narrador",
                        )
                
                with gr.Row():
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
            
            # Tab 3: Ayuda
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
                voice_type_input,
                narrator_gender_input,
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
