"""
Preprocesamiento de texto para TTS.

Basado en el proyecto audiobook-creator de Prakhar Sharma (GPL-3.0).
Adaptado para ai-audiobook-creator.
"""

import re
from typing import List


def preprocess_text_for_tts(text: str) -> str:
    """
    Preprocesa texto para añadir puntuación donde sea necesario y prevenir problemas de TTS.
    
    Esta función:
    - Añade puntos a títulos y encabezados de capítulos sin puntuación final
    - Añade puntos a líneas que no terminan con puntuación apropiada
    - Preserva puntuación existente y estructura de diálogos
    - Maneja casos especiales como abreviaturas y diálogos
    - Resuelve conflictos de dos puntos para formato de voz de Orpheus TTS
    
    Args:
        text: El texto a preprocesar
        
    Returns:
        El texto preprocesado con puntuación correcta
    """
    lines = text.split('\n')
    processed_lines = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Saltar líneas vacías
        if not line:
            processed_lines.append(line)
            continue
            
        # Manejar casos especiales donde no queremos añadir puntuación
        if _should_skip_punctuation(line):
            processed_lines.append(line)
            continue
            
        # Manejar conflictos de dos puntos para formato de voz de Orpheus TTS
        line = _resolve_colon_conflicts(line)
        
        # Mover puntuación de fuera de comillas a dentro para compatibilidad TTS
        line = _move_punctuation_inside_quotes(line)
            
        # Verificar si la línea termina con diálogo que tiene puntuación interna
        if _ends_with_punctuated_dialogue(line):
            processed_lines.append(line)
            continue
            
        # Verificar diálogo sin puntuación interna y añadirla
        if _is_unpunctuated_dialogue(line):
            line = _add_punctuation_inside_dialogue(line)
            processed_lines.append(line)
            continue
            
        # Verificar si la línea ya termina con puntuación correcta
        if line.endswith(('.', '!', '?', ':', ';', '…')):
            processed_lines.append(line)
            continue
            
        # Verificar si es un título o encabezado de capítulo
        if _is_title_or_heading(line, i, len(lines)):
            processed_lines.append(line + '.')
            continue
            
        # Verificar si la línea termina con coma (podría ser parte de una oración más grande)
        if line.endswith(','):
            processed_lines.append(line)
            continue
            
        # Por defecto: añadir punto si la línea no termina con puntuación
        processed_lines.append(line + '.')
    
    return '\n'.join(processed_lines)


def _should_skip_punctuation(line: str) -> bool:
    """Verificar si debemos saltar la adición de puntuación a esta línea."""
    # Saltar líneas que son solo números o muy cortas
    if len(line.strip()) <= 2:
        return True
        
    # Saltar líneas que terminan con abreviaturas comunes
    abbrev_pattern = r'\b(?:Mr|Mrs|Ms|Dr|Prof|Sr|Jr|Inc|Ltd|Co|etc|vs|vol|no|pp)\.$'
    if re.search(abbrev_pattern, line, re.IGNORECASE):
        return True
        
    return False


def _is_title_or_heading(line: str, line_index: int, total_lines: int) -> bool:
    """Verificar si esta línea es un título o encabezado de capítulo."""
    # La primera línea probablemente sea un título
    if line_index == 0:
        return True
        
    # Líneas que empiezan con "Chapter", "Capítulo", etc. son encabezados
    if re.match(r'^(Chapter|Capítulo|Part|Parte)\s+\d+', line, re.IGNORECASE):
        return True
        
    # Líneas cortas sin palabras comunes de oraciones podrían ser encabezados
    common_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
                   'el', 'la', 'los', 'las', 'un', 'una', 'y', 'o', 'pero', 'en', 'a', 'de', 'con', 'por']
    if len(line.split()) <= 6 and not any(word.lower() in line.lower() for word in common_words):
        if line_index > 0:
            return True
            
    return False


def _ends_with_punctuated_dialogue(line: str) -> bool:
    """Verificar si la línea termina con diálogo que ya tiene puntuación correcta."""
    # Patrón 1: Puntuación dentro de comillas
    dialogue_pattern1 = r'[.!?…]\s*[\'"]?"$'
    if re.search(dialogue_pattern1, line):
        return True
    
    # Patrón 2: Comillas seguidas de puntuación
    dialogue_pattern2 = r'[\'"][.!?…]$'
    if re.search(dialogue_pattern2, line):
        return True
        
    # Diálogo con atribución como: "Hola," dijo ella.
    attribution_pattern = r'",?\s+\w+\s+(said|asked|replied|whispered|shouted|exclaimed|muttered|declared|dijo|preguntó|respondió|susurró|gritó|exclamó|murmuró|declaró).*[.!?]$'
    if re.search(attribution_pattern, line, re.IGNORECASE):
        return True
        
    return False


def _is_unpunctuated_dialogue(line: str) -> bool:
    """Verificar si una línea es diálogo que carece de puntuación interna."""
    # Patrón: línea termina con comilla pero sin puntuación antes
    unpunctuated_dialogue_pattern = r'[^.!?…]["\']$'
    if re.search(unpunctuated_dialogue_pattern, line):
        return True
        
    return False


def _add_punctuation_inside_dialogue(line: str) -> str:
    """
    Añade puntuación dentro de comillas para diálogos sin puntuación.
    
    Transforma patrones como:
    - "Hola" → "Hola."
    - "¿Qué haces" → "¿Qué haces."
    
    Args:
        line: La línea de texto a procesar
        
    Returns:
        La línea con puntuación añadida dentro de comillas
    """
    # Añadir punto antes de la comilla de cierre si no hay puntuación
    line = re.sub(r'([^.!?…])(["\'])$', r'\1.\2', line)
    
    return line


def _resolve_colon_conflicts(line: str) -> str:
    """
    Resuelve conflictos de dos puntos para formato de voz de Orpheus TTS.
    
    Orpheus usa formato: <|audio|>voice_name: text content<|eot_id|>
    Los dos puntos en el contenido pueden confundir al parser.
    
    Args:
        line: La línea de texto a procesar
        
    Returns:
        La línea con todos los dos puntos reemplazados
    """
    # Manejar referencias de tiempo primero
    # "3:30 AM" -> "3.30 AM"
    time_pattern = r'\b(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)?\b'
    line = re.sub(time_pattern, r'\1.\2 \3', line).strip()
    
    # Manejar ratios o puntuaciones
    # "5:3" -> "5 a 3"
    ratio_pattern = r'\b(\d+):(\d+)\b'
    line = re.sub(ratio_pattern, r'\1 a \2', line)
    
    # Reemplazar todos los dos puntos restantes con guiones
    line = line.replace(':', ' -')
    
    # Limpiar espacios dobles
    line = re.sub(r'\s+', ' ', line).strip()
    
    return line


def _move_punctuation_inside_quotes(line: str) -> str:
    """
    Mueve puntuación de fuera de comillas a dentro para compatibilidad TTS.
    
    Transforma patrones como:
    - "Hola". → "Hola."
    - "¿Qué"? → "¿Qué?"
    
    Args:
        line: La línea de texto a procesar
        
    Returns:
        La línea con puntuación movida dentro de comillas
    """
    line = re.sub(r'(["\'])([.!?…])', r'\2\1', line)
    
    return line


def normalize_unicode_characters(text: str) -> str:
    """
    Normaliza caracteres Unicode especiales a sus equivalentes ASCII.
    
    Args:
        text: El texto a normalizar
        
    Returns:
        El texto con caracteres Unicode normalizados
    """
    replacements = {
        "\u201c": '"',  # Comilla izquierda
        "\u201d": '"',  # Comilla derecha
        "\u2019": "'",  # Apóstrofe curvo
        "\u2018": "'",  # Comilla simple izquierda
        "\u2014": "-",  # Guión largo (em dash)
        "\u2013": "-",  # Guión medio (en dash)
        "\u2026": "...",  # Puntos suspensivos
        "\u00a0": " ",  # Espacio sin ruptura
    }
    
    for unicode_char, replacement in replacements.items():
        text = text.replace(unicode_char, replacement)
    
    return text


def normalize_line_breaks(text: str) -> str:
    """
    Normaliza saltos de línea eliminando líneas vacías excesivas.
    
    Args:
        text: El texto a normalizar
        
    Returns:
        El texto con saltos de línea normalizados
    """
    lines = text.splitlines()
    non_empty_lines = [line.strip() for line in lines if line.strip()]
    return '\n'.join(non_empty_lines)


def fix_unterminated_quotes(text: str) -> str:
    """
    Arregla comillas sin cerrar en el texto.
    
    Args:
        text: El texto a corregir
        
    Returns:
        El texto con comillas corregidas
    """
    if not text:
        return text
    
    lines = text.splitlines()
    fixed_lines = []
    
    for line in lines:
        if not line.strip():
            continue
            
        total_quotes = line.count('"')
        
        # Si las comillas son pares, la línea está bien
        if total_quotes % 2 == 0:
            fixed_lines.append(line)
            continue
        
        # Si número impar de comillas y la línea termina con comilla
        if line.endswith('"'):
            # Añadir comilla al principio
            line = '"' + line
        else:
            # Si número impar pero no termina con comilla, añadir al final
            line += '"'
        
        fixed_lines.append(line)
    
    return "\n".join(fixed_lines)


def preprocess_full_text(text: str) -> str:
    """
    Aplica todo el preprocesamiento necesario al texto para TTS.
    
    Args:
        text: El texto completo a preprocesar
        
    Returns:
        El texto completamente preprocesado
    """
    # Paso 1: Normalizar Unicode
    text = normalize_unicode_characters(text)
    
    # Paso 2: Normalizar saltos de línea
    text = normalize_line_breaks(text)
    
    # Paso 3: Arreglar comillas sin cerrar
    text = fix_unterminated_quotes(text)
    
    # Paso 4: Preprocesar para TTS
    text = preprocess_text_for_tts(text)
    
    return text


def split_and_annotate_text(text: str) -> List[dict]:
    """
    Divide el texto en diálogo y narración, anotando cada segmento.
    
    Args:
        text: El texto a dividir
        
    Returns:
        Lista de diccionarios con 'text' y 'type' ('dialogue' o 'narration')
    """
    # Dividir manteniendo los diálogos (texto entre comillas)
    parts = re.split(r'("[^"]+")', text)
    annotated_parts = []

    for part in parts:
        if part:  # Ignorar strings vacíos
            annotated_parts.append({
                "text": part,
                "type": "dialogue" if part.startswith('"') and part.endswith('"') else "narration"
            })

    return annotated_parts


def is_only_punctuation(text: str) -> bool:
    """
    Verifica si una línea contiene solo signos de puntuación sin palabras.
    Esto ayuda a evitar errores de TTS con líneas que solo tienen puntuación.
    
    Args:
        text: La línea de texto a verificar
        
    Returns:
        True si la línea contiene solo puntuación, False de lo contrario
    """
    import string
    
    cleaned_text = text.strip()
    
    if not cleaned_text:
        return True
    
    # Conjunto extendido de puntuación incluyendo Unicode común en libros
    extended_punctuation = string.punctuation + '—–""''…‚„‹›«»‰‱'
    
    # Remover todos los signos de puntuación
    text_without_punct = ''.join(char for char in cleaned_text if char not in extended_punctuation)
    
    # Si no queda nada después de remover puntuación, es solo puntuación
    return len(text_without_punct.strip()) == 0
