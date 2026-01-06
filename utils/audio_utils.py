"""
Utilidades de audio para generación de audiobooks.

Incluye sistema de retry, generación de audio con separación diálogo/narración,
y detección de capítulos.

Basado en el proyecto audiobook-creator de Prakhar Sharma (GPL-3.0).
Adaptado para ai-audiobook-creator.
"""

import os
import re
import asyncio
import random
import traceback
from typing import Optional, Tuple, List, Dict, Any, TYPE_CHECKING

# Importación condicional de openai para evitar errores si no está instalado
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    AsyncOpenAI = None
    OPENAI_AVAILABLE = False

from .text_preprocessing import split_and_annotate_text, is_only_punctuation


# Configuración de reintentos
MAX_RETRIES = 3
BASE_DELAY = 0.1  # Delay base en segundos
MAX_DELAY = 10  # Delay máximo en segundos


async def generate_audio_with_retry(
    client: AsyncOpenAI, 
    tts_model: str, 
    text_to_speak: str, 
    voice_to_speak_in: str, 
    max_retries: int = MAX_RETRIES,
    speed: float = 0.85,
    timeout: int = 600
) -> bytearray:
    """
    Genera audio con mecanismo de reintentos y backoff exponencial.
    
    Args:
        client: Instancia del cliente AsyncOpenAI
        tts_model: El modelo TTS a usar
        text_to_speak: El texto a convertir en voz
        voice_to_speak_in: La voz a usar para TTS
        max_retries: Número máximo de intentos de reintento
        speed: Velocidad del audio (default 0.85)
        timeout: Timeout en segundos
        
    Returns:
        bytearray: Buffer de datos de audio
        
    Raises:
        Exception: Si todos los intentos de reintento fallan
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            # Crear un buffer en memoria para los datos de audio
            audio_buffer = bytearray()
            
            # Generar audio para la parte
            async with client.audio.speech.with_streaming_response.create(
                model=tts_model,
                voice=voice_to_speak_in,
                response_format="wav",
                speed=speed,
                input=text_to_speak,
                timeout=timeout
            ) as response:
                async for chunk in response.iter_bytes():
                    audio_buffer.extend(chunk)
            
            # Si llegamos aquí, la solicitud fue exitosa
            if attempt > 0:
                print(f"Audio generado exitosamente después de {attempt} intentos de reintento")
            
            return audio_buffer
            
        except Exception as e:
            traceback.print_exc()
            print(f"Error: {e}")
            last_exception = e
                        
            if attempt < max_retries:
                # Calcular delay con backoff exponencial y jitter
                delay = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
                # Añadir jitter para prevenir thundering herd
                jitter = random.uniform(0, 0.1) * delay
                total_delay = delay + jitter
                
                print(f"Error de conexión en intento {attempt + 1}/{max_retries + 1}: {e}")
                print(f"Reintentando en {total_delay:.2f} segundos...")
                
                await asyncio.sleep(total_delay)
                continue
            else:
                # Se alcanzó el máximo de reintentos o error no de conexión
                print(f"Fallo al generar audio después de {attempt + 1} intentos: {e}")
                break
    
    # Si llegamos aquí, todos los intentos de reintento fallaron
    raise Exception(f"Fallo al generar audio después de {max_retries + 1} intentos. Último error: {last_exception}")


async def generate_line_audio_with_voices(
    client: AsyncOpenAI,
    tts_model: str,
    line: str,
    narrator_voice: str,
    dialogue_voice: str,
    max_retries: int = MAX_RETRIES
) -> Optional[bytearray]:
    """
    Genera audio para una línea usando voces diferentes para narración y diálogo.
    
    Esta función divide la línea en partes de diálogo y narración,
    genera audio para cada parte con la voz correspondiente,
    y las combina en un solo buffer de audio.
    
    Args:
        client: Cliente AsyncOpenAI
        tts_model: Modelo TTS a usar
        line: Línea de texto a procesar
        narrator_voice: Voz para narración
        dialogue_voice: Voz para diálogos
        max_retries: Número máximo de reintentos
        
    Returns:
        bytearray: Buffer de audio combinado, o None si la línea está vacía/solo puntuación
    """
    if not line or is_only_punctuation(line):
        return None
    
    # Dividir la línea en partes anotadas
    annotated_parts = split_and_annotate_text(line)
    
    # Buffer combinado para toda la línea
    combined_buffer = bytearray()
    
    for part in annotated_parts:
        text_to_speak = part["text"].strip()
        
        if not text_to_speak or is_only_punctuation(text_to_speak):
            continue
        
        # Seleccionar voz según el tipo
        voice_to_use = narrator_voice if part["type"] == "narration" else dialogue_voice
        
        # Limpiar comillas dobles y backslashes del texto
        text_to_speak = text_to_speak.replace('"', '').replace('\\', '')
        
        try:
            # Generar audio para esta parte
            audio_buffer = await generate_audio_with_retry(
                client,
                tts_model,
                text_to_speak,
                voice_to_use,
                max_retries
            )
            
            combined_buffer.extend(audio_buffer)
            
        except Exception as e:
            print(f"Advertencia: Fallo al generar audio para texto: '{text_to_speak[:50]}...' - Error: {str(e)}")
            # Continuar con la siguiente parte
            continue
    
    if len(combined_buffer) == 0:
        return None
    
    return combined_buffer


def check_if_chapter_heading(text: str) -> bool:
    """
    Verifica si un texto dado representa un encabezado de capítulo.
    
    Un encabezado de capítulo se considera una cadena que empieza con 
    "Chapter", "Capítulo", "Part", "Parte" (case-insensitive) seguido
    de un número.
    
    Args:
        text: El texto a verificar
        
    Returns:
        True si el texto es un encabezado de capítulo, False de lo contrario
    """
    # Patrones para detectar encabezados de capítulo en español e inglés
    patterns = [
        r'^(Chapter|Capítulo)\s+([\w-]+|\d+)',
        r'^(Part|Parte)\s+([\w-]+|\d+)',
        r'^(Section|Sección)\s+([\w-]+|\d+)',
        r'^(Act|Acto)\s+([\w-]+|\d+)',
    ]
    
    for pattern in patterns:
        regex = re.compile(pattern, re.IGNORECASE)
        match = regex.match(text.strip())
        
        if match:
            label, number = match.groups()
            try:
                # Intentar convertir el número
                if number.isdigit():
                    int(number)
                    return True
                else:
                    # Intentar convertir palabras a números
                    try:
                        from word2number import w2n
                        w2n.word_to_num(number)
                        return True
                    except (ImportError, ValueError):
                        # Si word2number no está disponible o el número no es válido
                        # Verificar patrones comunes de números romanos
                        roman_pattern = r'^[IVXLCDM]+$'
                        if re.match(roman_pattern, number.upper()):
                            return True
            except ValueError:
                continue
    
    return False


def detect_chapters_in_text(text: str) -> List[Dict[str, Any]]:
    """
    Detecta todos los capítulos en un texto y retorna su estructura.
    
    Args:
        text: El texto completo a analizar
        
    Returns:
        Lista de diccionarios con información de cada capítulo:
        - 'title': Título del capítulo
        - 'start_line': Índice de la línea de inicio
        - 'lines': Lista de líneas en el capítulo
    """
    lines = text.split('\n')
    chapters = []
    current_chapter = {
        'title': 'Introducción',
        'start_line': 0,
        'lines': []
    }
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        if line_stripped and check_if_chapter_heading(line_stripped):
            # Guardar el capítulo anterior si tiene contenido
            if current_chapter['lines']:
                chapters.append(current_chapter)
            
            # Comenzar nuevo capítulo
            current_chapter = {
                'title': line_stripped,
                'start_line': i,
                'lines': [line_stripped]
            }
        else:
            current_chapter['lines'].append(line)
    
    # Añadir el último capítulo
    if current_chapter['lines']:
        chapters.append(current_chapter)
    
    return chapters


def sanitize_filename(text: str) -> str:
    """
    Limpia un texto para usarlo como nombre de archivo.
    
    Args:
        text: El texto a limpiar
        
    Returns:
        El texto limpio, seguro para usar como nombre de archivo
    """
    # Remover o reemplazar caracteres problemáticos
    text = text.replace("'", '').replace('"', '').replace('/', ' ').replace('.', ' ')
    text = text.replace(':', '').replace('?', '').replace('\\', '').replace('|', '')
    text = text.replace('*', '').replace('<', '').replace('>', '').replace('&', 'and')
    
    # Limpiar nombre de archivo basado en patrón seguro
    regex = r"[^a-zA-Z0-9\-_./\s]"
    text = re.sub(regex, ' ', text, 0, re.MULTILINE) 
    
    # Normalizar espacios en blanco y recortar
    text = ' '.join(text.split())
    
    return text


def add_chapter_markers(text: str) -> str:
    """
    Añade marcadores de capítulo al texto para procesamiento posterior.
    
    Args:
        text: El texto a procesar
        
    Returns:
        El texto con marcadores de capítulo añadidos
    """
    lines = text.split('\n')
    processed_lines = []
    
    for line in lines:
        line_stripped = line.strip()
        
        if line_stripped and check_if_chapter_heading(line_stripped):
            # Añadir marcador antes del encabezado de capítulo
            processed_lines.append(f"\n--- CHAPTER: {line_stripped} ---\n")
            processed_lines.append(line)
        else:
            processed_lines.append(line)
    
    return '\n'.join(processed_lines)


async def check_tts_service_health(
    client: AsyncOpenAI,
    tts_model: str,
    test_voice: str = "af_heart"
) -> Tuple[bool, str]:
    """
    Verifica si el servicio TTS está funcionando.
    
    Args:
        client: Cliente AsyncOpenAI
        tts_model: Modelo TTS a verificar
        test_voice: Voz de prueba a usar
        
    Returns:
        Tupla (is_healthy, message)
    """
    try:
        # Intentar generar un audio corto de prueba
        audio_buffer = bytearray()
        
        async with client.audio.speech.with_streaming_response.create(
            model=tts_model,
            voice=test_voice,
            response_format="wav",
            speed=1.0,
            input="Test.",
            timeout=30
        ) as response:
            async for chunk in response.iter_bytes():
                audio_buffer.extend(chunk)
        
        if len(audio_buffer) > 0:
            return True, "Servicio TTS funcionando correctamente"
        else:
            return False, "El servicio TTS respondió pero no generó audio"
            
    except Exception as e:
        return False, f"Error al conectar con el servicio TTS: {str(e)}"


def estimate_audio_duration(text: str, words_per_minute: int = 150) -> float:
    """
    Estima la duración del audio en minutos basado en el número de palabras.
    
    Args:
        text: El texto a estimar
        words_per_minute: Velocidad de lectura estimada (default 150 WPM)
        
    Returns:
        Duración estimada en minutos
    """
    word_count = len(text.split())
    return word_count / words_per_minute


def get_audio_generation_progress(
    current_line: int,
    total_lines: int,
    current_chapter: Optional[str] = None
) -> str:
    """
    Genera un mensaje de progreso para la generación de audio.
    
    Args:
        current_line: Línea actual siendo procesada
        total_lines: Total de líneas a procesar
        current_chapter: Nombre del capítulo actual (opcional)
        
    Returns:
        Mensaje de progreso formateado
    """
    percentage = (current_line / total_lines) * 100 if total_lines > 0 else 0
    
    if current_chapter:
        return f"Generando audio: {percentage:.1f}% - Capítulo: {current_chapter}"
    else:
        return f"Generando audio: {percentage:.1f}%"
