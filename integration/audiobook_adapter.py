"""
Adaptador que integra con el sistema de generación de audiobook existente.

Incluye funcionalidades mejoradas:
- Preprocesamiento de texto para TTS
- Separación diálogo/narración con voces diferentes
- Voice mapping avanzado
- Sistema de reintentos para generación de audio
- Detección automática de capítulos
"""

import os
import sys
import asyncio
import shutil
from typing import Optional, Dict, Any, AsyncGenerator
from pathlib import Path

from utils.rich_logger import get_logger

# Agregar el directorio del proyecto original al path para importar sus módulos
ORIGINAL_PROJECT_PATH = Path(__file__).parent.parent.parent / "audiobook-creator"
if str(ORIGINAL_PROJECT_PATH) not in sys.path:
    sys.path.insert(0, str(ORIGINAL_PROJECT_PATH))

# Intentar importar desde el proyecto original
try:
    sys.path.insert(0, str(ORIGINAL_PROJECT_PATH))
    from generate_audiobook import (
        generate_audio_with_single_voice,
        generate_audio_with_multiple_voices,
    )
    ORIGINAL_AVAILABLE = True
except ImportError:
    generate_audio_with_single_voice = None
    generate_audio_with_multiple_voices = None
    ORIGINAL_AVAILABLE = False

# Importar nuestros módulos locales
from utils.language_support import LanguageSupport
from utils.text_preprocessing import (
    preprocess_full_text,
    split_and_annotate_text,
    is_only_punctuation,
)
from utils.voice_mapping import (
    get_narrator_and_dialogue_voices,
    get_tts_model_from_env,
)
from utils.audio_utils import (
    generate_audio_with_retry,
    generate_line_audio_with_voices,
    check_if_chapter_heading,
    detect_chapters_in_text,
    sanitize_filename,
    check_tts_service_health,
    get_audio_generation_progress,
)


class AudiobookAdapter:
    """
    Adaptador para generar audiobooks.
    
    Puede usar el proyecto audiobook-creator original si está disponible,
    o generar audio usando nuestros propios módulos.
    """
    
    def __init__(self):
        """Inicializa el adaptador."""
        self.original_project_path = ORIGINAL_PROJECT_PATH
        self.tts_model = get_tts_model_from_env()
        self.use_original = ORIGINAL_AVAILABLE
    
    async def generate_audiobook(
        self,
        text_file_path: str,
        output_format: str = "mp3",
        voice_type: str = "Single Voice",
        narrator_gender: str = "female",
        language: str = "es",
        add_emotion_tags: bool = False,
        voice_id: Optional[str] = None,
        output_filename: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Genera un audiobook a partir del archivo de texto formateado.
        
        Args:
            text_file_path: Ruta al archivo de texto formateado
            output_format: Formato de salida (mp3, m4a, wav, etc.)
            voice_type: Tipo de voz ("Single Voice" o "Multi-Voice")
            narrator_gender: Género del narrador ("male" o "female")
            language: Idioma del contenido
            add_emotion_tags: Si se deben agregar etiquetas de emoción
            voice_id: ID específico de la voz a usar (ej: "em_alex", "ef_dora")
            output_filename: Nombre del archivo de salida (sin extensión)
            
        Yields:
            Actualizaciones de progreso
        """
        logger = get_logger()
        
        logger.section("🎧 Generación de Audiobook")
        logger.info(f"Archivo de texto: {text_file_path}")
        logger.info(f"Formato: {output_format} | Voz: {voice_type} | Género: {narrator_gender}")
        logger.info(f"Idioma: {language} | Motor TTS: {self.tts_model}")
        
        # Verificar que el archivo existe
        if not os.path.exists(text_file_path):
            logger.error(f"El archivo de texto no existe: {text_file_path}")
            raise FileNotFoundError(f"El archivo de texto no existe: {text_file_path}")
        
        # Asegurar que existe el directorio de salida
        os.makedirs("generated_audiobooks", exist_ok=True)
        
        # Leer y preprocesar el texto
        with open(text_file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        text_length = len(text)
        word_count = len(text.split())
        logger.info(f"Texto cargado: {word_count} palabras ({text_length} caracteres)")
        
        # Aplicar preprocesamiento con el idioma correcto
        logger.step("Preprocesando texto para TTS")
        yield "🔧 Preprocesando texto para TTS..."
        text = preprocess_full_text(text, language)
        
        # Guardar el texto preprocesado
        with open("converted_book.txt", 'w', encoding='utf-8') as f:
            f.write(text)
        logger.success("Texto preprocesado y guardado")
        yield "✅ Texto preprocesado y guardado"
        
        # Detectar capítulos
        chapters = detect_chapters_in_text(text)
        logger.info(f"Detectados {len(chapters)} capítulo(s)")
        yield f"📚 Detectados {len(chapters)} capítulo(s)"
        
        # Configurar variables de entorno para TTS si es necesario
        self._setup_tts_environment(language)
        
        # Determinar si generar M4B o formato estándar
        generate_m4b = output_format.lower() == "m4b"
        
        # Intentar usar el proyecto original si está disponible
        if self.use_original and generate_audio_with_single_voice is not None:
            yield "🎧 Usando motor de generación audiobook-creator..."
            
            try:
                if voice_type == "Single Voice":
                    async for progress in generate_audio_with_single_voice(
                        output_format=output_format.lower() if not generate_m4b else "m4a",
                        narrator_gender=narrator_gender,
                        generate_m4b_audiobook_file=generate_m4b,
                        book_path="",
                        add_emotion_tags=add_emotion_tags,
                    ):
                        yield progress
                else:
                    # Multi-Voice usando el proyecto original
                    async for progress in generate_audio_with_single_voice(
                        output_format=output_format.lower() if not generate_m4b else "m4a",
                        narrator_gender=narrator_gender,
                        generate_m4b_audiobook_file=generate_m4b,
                        book_path="",
                        add_emotion_tags=add_emotion_tags,
                    ):
                        yield progress
                
                # Determinar ruta del archivo generado
                if generate_m4b:
                    output_path = "generated_audiobooks/audiobook.m4b"
                else:
                    output_path = f"generated_audiobooks/audiobook.{output_format.lower()}"
                
                if os.path.exists(output_path):
                    yield f"✅ Audiobook generado exitosamente: {output_path}"
                else:
                    yield "⚠️ El proceso terminó pero no se encontró el archivo de salida"
                    
            except Exception as e:
                yield f"⚠️ Error con motor original: {str(e)}"
                yield "🔄 Intentando con motor alternativo..."
                # Fallback a nuestro propio motor
                async for progress in self._generate_audiobook_native(
                    text=text,
                    output_format=output_format,
                    voice_type=voice_type,
                    narrator_gender=narrator_gender,
                    language=language,
                ):
                    yield progress
        else:
            # Usar nuestro propio motor de generación
            yield "🎧 Usando motor de generación nativo..."
            async for progress in self._generate_audiobook_native(
                text=text,
                output_format=output_format,
                voice_type=voice_type,
                narrator_gender=narrator_gender,
                language=language,
            ):
                yield progress
    
    async def _generate_audiobook_native(
        self,
        text: str,
        output_format: str = "mp3",
        voice_type: str = "Single Voice",
        narrator_gender: str = "female",
        language: str = "es",
    ) -> AsyncGenerator[str, None]:
        """
        Genera un audiobook usando nuestros propios módulos.
        
        Esta es una implementación nativa que no depende del proyecto original.
        Usa las funcionalidades de audio_utils y voice_mapping.
        
        Args:
            text: El texto a convertir en audio
            output_format: Formato de salida
            voice_type: Tipo de voz
            narrator_gender: Género del narrador
            language: Idioma
            
        Yields:
            Actualizaciones de progreso
        """
        logger = get_logger()
        
        try:
            from openai import AsyncOpenAI
            
            # Configurar cliente TTS
            tts_base_url = os.environ.get("TTS_BASE_URL", "http://localhost:8880/v1")
            tts_api_key = os.environ.get("TTS_API_KEY", "not-needed")
            
            logger.info(f"Conectando con servicio TTS en: {tts_base_url}")
            client = AsyncOpenAI(base_url=tts_base_url, api_key=tts_api_key)
            
            # Verificar salud del servicio TTS
            logger.step("Verificando servicio TTS")
            yield "🔍 Verificando servicio TTS..."
            is_healthy, message = await check_tts_service_health(client, self.tts_model)
            
            if not is_healthy:
                logger.error(f"Servicio TTS no disponible: {message}")
                yield f"❌ {message}"
                return
            
            logger.success(f"Servicio TTS: {message}")
            yield f"✅ {message}"
            
            # Obtener voces - usar la voz específica del idioma si está disponible
            from utils.voice_mapping import get_default_voice_for_language
            
            # Usar la voz por defecto del idioma seleccionado
            narrator_voice = get_default_voice_for_language(self.tts_model, language, narrator_gender)
            dialogue_voice = narrator_voice  # Usar la misma voz para diálogos en modo simple
            
            logger.info(f"Voces configuradas para idioma '{language}' - Narrador: {narrator_voice}")
            yield f"🎤 Voces configuradas para idioma '{language}' - Narrador: {narrator_voice}"
            
            # Dividir en líneas
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            total_lines = len(lines)
            
            logger.tts_start(self.tts_model, len(text))
            yield f"📝 Procesando {total_lines} líneas..."
            
            # Generar audio para cada línea
            audio_segments = []
            processed = 0
            errors = 0
            
            for i, line in enumerate(lines):
                if not line or is_only_punctuation(line):
                    continue
                
                try:
                    # Generar audio con separación diálogo/narración
                    audio_buffer = await generate_line_audio_with_voices(
                        client=client,
                        tts_model=self.tts_model,
                        line=line,
                        narrator_voice=narrator_voice,
                        dialogue_voice=dialogue_voice,
                    )
                    
                    if audio_buffer:
                        audio_segments.append(audio_buffer)
                    
                    processed += 1
                    
                    # Reportar progreso cada 10 líneas
                    if processed % 10 == 0:
                        logger.tts_progress(processed, total_lines, line[:50] if line else "")
                        progress_msg = get_audio_generation_progress(processed, total_lines)
                        yield progress_msg
                        
                except Exception as e:
                    errors += 1
                    logger.warning(f"Error en línea {i}: {str(e)}")
                    yield f"⚠️ Error en línea {i}: {str(e)}"
                    continue
            
            logger.tts_complete()
            logger.success(f"Procesadas {processed} líneas ({errors} errores)")
            yield f"✅ Procesadas {processed} líneas"
            
            # Combinar segmentos de audio
            if audio_segments:
                logger.audio_processing("Combinando segmentos de audio", f"{len(audio_segments)} segmentos")
                yield "🔧 Combinando segmentos de audio..."
                
                # Combinar todos los buffers
                combined_audio = bytearray()
                for segment in audio_segments:
                    combined_audio.extend(segment)
                
                audio_size_mb = len(combined_audio) / (1024 * 1024)
                logger.info(f"Audio combinado: {audio_size_mb:.2f} MB")
                
                # Guardar archivo temporal WAV
                temp_wav_path = "generated_audiobooks/audiobook_temp.wav"
                with open(temp_wav_path, 'wb') as f:
                    f.write(combined_audio)
                
                # Convertir formato si es necesario
                output_path = f"generated_audiobooks/audiobook.{output_format.lower()}"
                
                if output_format.lower() != "wav":
                    logger.audio_processing(f"Convirtiendo a {output_format}")
                    yield f"🔄 Convirtiendo a {output_format}..."
                    # Usar ffmpeg para conversión
                    import subprocess
                    try:
                        subprocess.run([
                            "ffmpeg", "-y", "-i", temp_wav_path,
                            "-acodec", "libmp3lame" if output_format.lower() == "mp3" else "copy",
                            output_path
                        ], capture_output=True, check=True)
                        os.remove(temp_wav_path)
                        logger.success(f"Convertido exitosamente a {output_format}")
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        # Si ffmpeg no está disponible, renombrar WAV
                        logger.warning("ffmpeg no disponible, guardando como WAV")
                        yield "⚠️ ffmpeg no disponible, guardando como WAV"
                        output_path = temp_wav_path
                else:
                    shutil.move(temp_wav_path, output_path)
                
                # Obtener tamaño final del archivo
                if os.path.exists(output_path):
                    final_size_mb = os.path.getsize(output_path) / (1024 * 1024)
                    logger.success(f"Audiobook generado: {output_path} ({final_size_mb:.2f} MB)")
                
                yield f"✅ Audiobook generado exitosamente: {output_path}"
            else:
                logger.error("No se generaron segmentos de audio")
                yield "❌ No se generaron segmentos de audio"
                
        except ImportError:
            logger.error("El paquete openai no está instalado")
            yield "❌ Error: openai no está instalado"
        except Exception as e:
            logger.error(f"Error en generación de audio: {str(e)}")
            yield f"❌ Error: {str(e)}"
    
    def _setup_tts_environment(self, language: str):
        """
        Configura variables de entorno para TTS según el idioma.
        
        Args:
            language: Código de idioma
        """
        # Obtener configuración TTS del idioma
        tts_config = LanguageSupport.get_tts_config(language)
        
        # Las variables de entorno ya deberían estar configuradas en .env
        # pero podemos ajustar según el idioma si es necesario
    
    async def generate_audiobook_from_content(
        self,
        content_file_path: str,
        output_format: str = "mp3",
        voice_type: str = "Single Voice",
        narrator_gender: str = "female",
        language: str = "es",
        add_emotion_tags: bool = False,
    ) -> Dict[str, Any]:
        """
        Genera un audiobook completo desde el contenido formateado.
        
        Args:
            content_file_path: Ruta al archivo de contenido formateado
            output_format: Formato de salida
            voice_type: Tipo de voz
            narrator_gender: Género del narrador
            language: Idioma
            add_emotion_tags: Si agregar etiquetas de emoción
            
        Returns:
            Diccionario con información del audiobook generado
        """
        # Asegurar que el archivo converted_book.txt existe
        if content_file_path != "converted_book.txt":
            shutil.copy(content_file_path, "converted_book.txt")
        
        # Generar audiobook
        output_path = None
        async for progress in self.generate_audiobook(
            text_file_path="converted_book.txt",
            output_format=output_format,
            voice_type=voice_type,
            narrator_gender=narrator_gender,
            language=language,
            add_emotion_tags=add_emotion_tags,
        ):
            if "exitosamente" in progress.lower() or "successfully" in progress.lower():
                if output_format.lower() == "m4b":
                    output_path = "generated_audiobooks/audiobook.m4b"
                else:
                    output_path = f"generated_audiobooks/audiobook.{output_format.lower()}"
        
        return {
            "output_path": output_path,
            "format": output_format,
            "voice_type": voice_type,
            "language": language,
        }
    
    def get_available_voices(self) -> Dict[str, Any]:
        """
        Obtiene las voces disponibles para el motor TTS actual.
        
        Returns:
            Diccionario con información de voces disponibles
        """
        from utils.voice_mapping import get_available_voices
        return get_available_voices(self.tts_model)
    
    def is_original_available(self) -> bool:
        """
        Verifica si el proyecto original está disponible.
        
        Returns:
            True si el proyecto original está disponible
        """
        return self.use_original and ORIGINAL_AVAILABLE
