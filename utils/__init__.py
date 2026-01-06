"""
Utilidades compartidas del sistema.
"""

# Importaciones condicionales para evitar errores de dependencias faltantes
try:
    from .llm_client import LLMClient
except ImportError:
    LLMClient = None

try:
    from .language_support import LanguageSupport, get_language_config
except ImportError:
    LanguageSupport = None
    get_language_config = None

# Nuevos módulos para funcionalidades avanzadas de audiobook (sin dependencias externas)
from .text_preprocessing import (
    preprocess_text_for_tts,
    preprocess_full_text,
    normalize_unicode_characters,
    normalize_line_breaks,
    fix_unterminated_quotes,
    split_and_annotate_text,
    is_only_punctuation,
)

from .voice_mapping import (
    load_voice_mappings,
    get_narrator_and_dialogue_voices,
    get_voice_for_character_score,
    get_narrator_voice_for_character,
    find_voice_for_character,
    get_available_voices,
    get_tts_model_from_env,
    validate_voice,
)

# Audio utils tiene dependencia de openai, importar condicionalmente
try:
    from .audio_utils import (
        generate_audio_with_retry,
        generate_line_audio_with_voices,
        check_if_chapter_heading,
        detect_chapters_in_text,
        sanitize_filename,
        add_chapter_markers,
        check_tts_service_health,
        estimate_audio_duration,
        get_audio_generation_progress,
        MAX_RETRIES,
    )
except ImportError:
    # Si openai no está instalado, importar solo las funciones que no lo requieren
    from .audio_utils import (
        check_if_chapter_heading,
        detect_chapters_in_text,
        sanitize_filename,
        add_chapter_markers,
        estimate_audio_duration,
        get_audio_generation_progress,
    )
    generate_audio_with_retry = None
    generate_line_audio_with_voices = None
    check_tts_service_health = None
    MAX_RETRIES = 3

__all__ = [
    # Clientes y soporte (opcionales)
    "LLMClient",
    "LanguageSupport",
    "get_language_config",
    
    # Preprocesamiento de texto
    "preprocess_text_for_tts",
    "preprocess_full_text",
    "normalize_unicode_characters",
    "normalize_line_breaks",
    "fix_unterminated_quotes",
    "split_and_annotate_text",
    "is_only_punctuation",
    
    # Voice mapping
    "load_voice_mappings",
    "get_narrator_and_dialogue_voices",
    "get_voice_for_character_score",
    "get_narrator_voice_for_character",
    "find_voice_for_character",
    "get_available_voices",
    "get_tts_model_from_env",
    "validate_voice",
    
    # Audio utilities
    "generate_audio_with_retry",
    "generate_line_audio_with_voices",
    "check_if_chapter_heading",
    "detect_chapters_in_text",
    "sanitize_filename",
    "add_chapter_markers",
    "check_tts_service_health",
    "estimate_audio_duration",
    "get_audio_generation_progress",
    "MAX_RETRIES",
]
