"""
Voice Mapping para TTS.

Sistema de mapeo de voces para diferentes motores TTS (Kokoro, Orpheus).
Permite asignar voces diferentes para narración y diálogos, así como
mapeo avanzado basado en scores de género para múltiples personajes.

Basado en el proyecto audiobook-creator de Prakhar Sharma (GPL-3.0).
Adaptado para ai-audiobook-creator.
"""

import os
import json
from typing import Tuple, Dict, Any, Optional
from pathlib import Path


def get_voice_map_path() -> Path:
    """Obtiene la ruta al archivo voice_map.json."""
    # Intentar primero en static_files relativo al módulo
    module_dir = Path(__file__).parent.parent
    voice_map_path = module_dir / "static_files" / "voice_map.json"
    
    if voice_map_path.exists():
        return voice_map_path
    
    # Fallback a ruta absoluta
    return Path("/home/oscar/work/wot/projects/audiobook/ai-audiobook-creator/static_files/voice_map.json")


def load_voice_mappings() -> Dict[str, Any]:
    """
    Carga los mapeos de voz desde el archivo JSON.
    
    Returns:
        Diccionario con los mapeos de voz para cada motor TTS
    """
    voice_map_path = get_voice_map_path()
    
    if not voice_map_path.exists():
        # Retornar mapeo por defecto si no existe el archivo
        return get_default_voice_mappings()
    
    with open(voice_map_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_default_voice_mappings() -> Dict[str, Any]:
    """
    Retorna mapeos de voz por defecto.
    
    Returns:
        Diccionario con mapeos de voz por defecto
    """
    return {
        "kokoro": {
            "male_narrator": "am_puck",
            "male_dialogue": "af_alloy+am_puck",
            "female_narrator": "af_heart",
            "female_dialogue": "af_sky",
            "male_score_map": {
                "0": "am_puck",
                "1": "am_onyx",
                "2": "am_michael",
                "3": "am_echo",
                "4": "am_fenrir+bf_alice",
                "5": "af_alloy+am_puck",
                "6": "af_kore",
                "7": "af_sky",
                "8": "af_aoede+af_heart",
                "9": "af_sarah",
                "10": "af_bella"
            },
            "female_score_map": {
                "0": "af_heart",
                "1": "am_onyx",
                "2": "am_echo",
                "3": "am_puck",
                "4": "am_fenrir+bf_alice",
                "5": "af_alloy+am_puck",
                "6": "af_kore",
                "7": "af_sky",
                "8": "af_aoede+af_heart",
                "9": "af_sarah",
                "10": "af_bella"
            }
        },
        "orpheus": {
            "male_narrator": "zac",
            "male_dialogue": "dan",
            "female_narrator": "tara",
            "female_dialogue": "leah",
            "male_score_map": {
                "0": "zac",
                "1": "leo",
                "2": "dan",
                "3": "dan",
                "4": "zac",
                "5": "zoe",
                "6": "jess",
                "7": "tara",
                "8": "tara",
                "9": "leah",
                "10": "mia"
            },
            "female_score_map": {
                "0": "tara",
                "1": "leo",
                "2": "dan",
                "3": "zac",
                "4": "zac",
                "5": "zoe",
                "6": "jess",
                "7": "jess",
                "8": "leah",
                "9": "leah",
                "10": "mia"
            }
        }
    }


def get_narrator_and_dialogue_voices(
    engine_name: str, 
    narrator_gender: str
) -> Tuple[str, str]:
    """
    Obtiene las voces de narrador y diálogo para modo single-voice.
    
    Args:
        engine_name: Nombre del motor TTS ("kokoro" o "orpheus")
        narrator_gender: Género del narrador ("male" o "female")
    
    Returns:
        Tupla (narrator_voice, dialogue_voice)
        
    Raises:
        ValueError: Si el motor no está en los mapeos de voz
    """
    voice_mappings = load_voice_mappings()
    
    engine_name_lower = engine_name.lower()
    
    if engine_name_lower not in voice_mappings:
        raise ValueError(f"Motor '{engine_name}' no encontrado en mapeos de voz. "
                        f"Motores disponibles: {list(voice_mappings.keys())}")
    
    engine_voices = voice_mappings[engine_name_lower]
    
    if narrator_gender == "male":
        narrator_voice = engine_voices["male_narrator"]
        dialogue_voice = engine_voices["male_dialogue"]
    else:  # female
        narrator_voice = engine_voices["female_narrator"]
        dialogue_voice = engine_voices["female_dialogue"]
    
    return narrator_voice, dialogue_voice


def get_voice_for_character_score(
    engine_name: str, 
    narrator_gender: str, 
    character_gender_score: int
) -> str:
    """
    Obtiene la voz para un personaje basado en la preferencia de género del narrador 
    y el score de género del personaje para modo multi-voice.
    
    El narrator_gender determina qué mapa de scores usar (male_score_map vs female_score_map),
    mientras que character_gender_score determina qué voz dentro de ese mapa.
    
    Args:
        engine_name: Nombre del motor TTS ("kokoro" o "orpheus")
        narrator_gender: Preferencia de género del narrador del usuario ("male" o "female")
        character_gender_score: Score de género del personaje (0-10)
    
    Returns:
        Identificador de voz para el personaje
        
    Raises:
        ValueError: Si el motor no está en los mapeos de voz
    """
    voice_mappings = load_voice_mappings()
    
    engine_name_lower = engine_name.lower()
    
    if engine_name_lower not in voice_mappings:
        raise ValueError(f"Motor '{engine_name}' no encontrado en mapeos de voz")
    
    engine_voices = voice_mappings[engine_name_lower]
    
    # Seleccionar el mapa de scores apropiado basado en la preferencia de género del NARRADOR
    if narrator_gender == "male":
        score_map = engine_voices["male_score_map"]
    else:  # female
        score_map = engine_voices["female_score_map"]
    
    # Convertir score a string para búsqueda de clave JSON
    score_key = str(character_gender_score)
    
    if score_key in score_map:
        return score_map[score_key]
    else:
        # Fallback a voz del narrador (score 0) si el score del personaje no se encuentra
        return score_map["0"]


def get_narrator_voice_for_character(
    engine_name: str, 
    narrator_gender: str
) -> str:
    """
    Obtiene la voz del narrador basada en la preferencia de género del usuario.
    
    Args:
        engine_name: Nombre del motor TTS ("kokoro" o "orpheus")
        narrator_gender: Preferencia de género del narrador del usuario ("male" o "female")
    
    Returns:
        Identificador de voz para el narrador (score 0 del mapa de scores apropiado)
    """
    voice_mappings = load_voice_mappings()
    
    engine_name_lower = engine_name.lower()
    
    if engine_name_lower not in voice_mappings:
        raise ValueError(f"Motor '{engine_name}' no encontrado en mapeos de voz")
    
    engine_voices = voice_mappings[engine_name_lower]
    
    # Seleccionar el mapa de scores apropiado basado en preferencia de género del narrador
    if narrator_gender == "male":
        score_map = engine_voices["male_score_map"]
    else:  # female
        score_map = engine_voices["female_score_map"]
    
    # Retornar la voz del narrador (score 0)
    return score_map["0"]


def find_voice_for_character(
    character_name: str,
    character_gender_map: Dict[str, Any],
    engine_name: str,
    narrator_gender: str
) -> str:
    """
    Encuentra la voz apropiada para un personaje basándose en su score de género.
    
    Args:
        character_name: Nombre del personaje
        character_gender_map: Diccionario mapeando nombres de personajes a sus scores de género
        engine_name: Nombre del motor TTS
        narrator_gender: Preferencia de género del narrador del usuario
    
    Returns:
        Identificador de voz que coincide con el score de género del personaje
    """
    # Manejar el personaje narrador especialmente
    if character_name.lower() == "narrator" or character_name.lower() == "narrador":
        return get_narrator_voice_for_character(engine_name, narrator_gender)
    
    # Obtener el score de género del personaje
    if "scores" in character_gender_map and character_name.lower() in character_gender_map["scores"]:
        character_info = character_gender_map["scores"][character_name.lower()]
        character_gender_score = character_info.get("gender_score", 5)
        
        return get_voice_for_character_score(engine_name, narrator_gender, character_gender_score)
    else:
        # Fallback para personajes desconocidos - usar score 5 (neutral)
        return get_voice_for_character_score(engine_name, narrator_gender, 5)


def get_available_voices(engine_name: str) -> Dict[str, Any]:
    """
    Obtiene todas las voces disponibles para un motor TTS.
    
    Args:
        engine_name: Nombre del motor TTS
        
    Returns:
        Diccionario con las voces disponibles
    """
    voice_mappings = load_voice_mappings()
    
    engine_name_lower = engine_name.lower()
    
    if engine_name_lower not in voice_mappings:
        return {}
    
    engine_voices = voice_mappings[engine_name_lower]
    
    # Recopilar todas las voces únicas
    all_voices = set()
    
    # Voces de narrador y diálogo
    all_voices.add(engine_voices.get("male_narrator", ""))
    all_voices.add(engine_voices.get("female_narrator", ""))
    all_voices.add(engine_voices.get("male_dialogue", ""))
    all_voices.add(engine_voices.get("female_dialogue", ""))
    
    # Voces de los mapas de scores
    for score_map_key in ["male_score_map", "female_score_map"]:
        if score_map_key in engine_voices:
            for voice in engine_voices[score_map_key].values():
                all_voices.add(voice)
    
    # Remover strings vacíos
    all_voices.discard("")
    
    return {"voices": list(all_voices)}


def get_tts_model_from_env() -> str:
    """
    Obtiene el modelo TTS configurado desde las variables de entorno.
    
    Returns:
        Nombre del modelo TTS (por defecto "kokoro")
    """
    return os.environ.get("TTS_MODEL", "kokoro").lower()


def validate_voice(engine_name: str, voice: str) -> bool:
    """
    Valida si una voz es válida para un motor TTS dado.
    
    Args:
        engine_name: Nombre del motor TTS
        voice: Identificador de la voz a validar
        
    Returns:
        True si la voz es válida, False de lo contrario
    """
    available = get_available_voices(engine_name)
    return voice in available.get("voices", [])
