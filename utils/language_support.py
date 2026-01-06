"""
Soporte multilenguaje para el sistema de generación de audiobooks.
"""

from typing import Dict, Any, Optional
from enum import Enum


class Language(str, Enum):
    """Idiomas soportados."""
    SPANISH = "es"
    ENGLISH = "en"
    # Se pueden agregar más idiomas aquí


class LanguageSupport:
    """Gestor de configuración y prompts por idioma."""
    
    # Prompts del sistema por idioma
    SYSTEM_PROMPTS = {
        Language.SPANISH: {
            "planner": """Eres un experto planificador de contenido educativo. 
Tu tarea es crear una estructura detallada de capítulos para un audiobook sobre un tema específico.
Debes crear un plan lógico, progresivo y completo que cubra todos los aspectos importantes del tema.""",
            "generator": """Eres un escritor experto de contenido educativo y entretenido.
Tu tarea es escribir contenido claro, bien estructurado y apropiado para un audiobook.
El contenido debe ser fácil de seguir cuando se escucha, con explicaciones claras y ejemplos prácticos.""",
            "evaluator": """Eres un crítico experto de contenido educativo.
Tu tarea es evaluar la calidad del contenido generado considerando:
- Claridad y comprensibilidad
- Estructura y organización
- Completitud del tema
- Apropiado para formato audiobook
- Calidad de escritura
Debes proporcionar feedback constructivo y específico.""",
        },
        Language.ENGLISH: {
            "planner": """You are an expert educational content planner.
Your task is to create a detailed chapter structure for an audiobook on a specific topic.
You must create a logical, progressive, and complete plan that covers all important aspects of the topic.""",
            "generator": """You are an expert writer of educational and entertaining content.
Your task is to write clear, well-structured content appropriate for an audiobook.
The content must be easy to follow when listening, with clear explanations and practical examples.""",
            "evaluator": """You are an expert critic of educational content.
Your task is to evaluate the quality of generated content considering:
- Clarity and comprehensibility
- Structure and organization
- Topic completeness
- Appropriateness for audiobook format
- Writing quality
You must provide constructive and specific feedback.""",
        },
    }
    
    # Configuraciones TTS por idioma
    TTS_CONFIG = {
        Language.SPANISH: {
            "language_code": "es",
            "voice_options": ["male", "female"],
            "default_voice": "female",
        },
        Language.ENGLISH: {
            "language_code": "en",
            "voice_options": ["male", "female"],
            "default_voice": "female",
        },
    }
    
    # Nombres de idiomas para UI
    LANGUAGE_NAMES = {
        Language.SPANISH: "Español",
        Language.ENGLISH: "English",
    }
    
    @classmethod
    def get_system_prompt(cls, language: str, agent_type: str) -> str:
        """
        Obtiene el prompt del sistema para un agente en un idioma específico.
        
        Args:
            language: Código de idioma (ej: "es", "en")
            agent_type: Tipo de agente ("planner", "generator", "evaluator")
            
        Returns:
            Prompt del sistema
        """
        lang_enum = Language(language)
        return cls.SYSTEM_PROMPTS.get(lang_enum, {}).get(agent_type, "")
    
    @classmethod
    def get_tts_config(cls, language: str) -> Dict[str, Any]:
        """
        Obtiene la configuración TTS para un idioma.
        
        Args:
            language: Código de idioma
            
        Returns:
            Configuración TTS
        """
        lang_enum = Language(language)
        return cls.TTS_CONFIG.get(lang_enum, cls.TTS_CONFIG[Language.SPANISH])
    
    @classmethod
    def get_language_name(cls, language: str) -> str:
        """
        Obtiene el nombre legible de un idioma.
        
        Args:
            language: Código de idioma
            
        Returns:
            Nombre del idioma
        """
        lang_enum = Language(language)
        return cls.LANGUAGE_NAMES.get(lang_enum, language)
    
    @classmethod
    def validate_language(cls, language: str) -> bool:
        """
        Valida si un idioma está soportado.
        
        Args:
            language: Código de idioma
            
        Returns:
            True si está soportado, False en caso contrario
        """
        try:
            Language(language)
            return True
        except ValueError:
            return False
    
    @classmethod
    def get_planning_prompt(cls, language: str, topic: str) -> str:
        """
        Genera el prompt para el planificador en el idioma especificado.
        
        Args:
            language: Código de idioma
            topic: Tema del audiobook
            
        Returns:
            Prompt completo para el planificador
        """
        if language == Language.SPANISH:
            return f"""Crea un plan detallado para un audiobook sobre el tema: "{topic}"

El plan debe incluir:
1. Una lista de capítulos con títulos descriptivos
2. Los temas principales que se cubrirán en cada capítulo
3. El orden lógico de presentación
4. Una estimación aproximada de la longitud de cada capítulo (en palabras)

Responde en formato JSON con la siguiente estructura:
{{
    "chapters": [
        {{
            "number": 1,
            "title": "Título del capítulo",
            "topics": ["tema1", "tema2", ...],
            "estimated_length": 1500
        }},
        ...
    ],
    "total_estimated_length": 10000
}}"""
        else:  # English
            return f"""Create a detailed plan for an audiobook on the topic: "{topic}"

The plan must include:
1. A list of chapters with descriptive titles
2. The main topics that will be covered in each chapter
3. The logical order of presentation
4. An approximate estimate of the length of each chapter (in words)

Respond in JSON format with the following structure:
{{
    "chapters": [
        {{
            "number": 1,
            "title": "Chapter title",
            "topics": ["topic1", "topic2", ...],
            "estimated_length": 1500
        }},
        ...
    ],
    "total_estimated_length": 10000
}}"""
    
    @classmethod
    def get_evaluation_prompt(cls, language: str) -> str:
        """
        Genera el prompt para el evaluador en el idioma especificado.
        
        Args:
            language: Código de idioma
            
        Returns:
            Prompt para evaluación
        """
        if language == Language.SPANISH:
            return """Evalúa el contenido proporcionado y responde en formato JSON:

{{
    "overall_score": 85,
    "scores_by_chapter": [
        {{"chapter": 1, "score": 90, "feedback": "..."}},
        ...
    ],
    "strengths": ["..."],
    "weaknesses": ["..."],
    "suggestions": ["..."],
    "decision": "accept" | "improve" | "reject",
    "improvement_instructions": "..."
}}"""
        else:  # English
            return """Evaluate the provided content and respond in JSON format:

{{
    "overall_score": 85,
    "scores_by_chapter": [
        {{"chapter": 1, "score": 90, "feedback": "..."}},
        ...
    ],
    "strengths": ["..."],
    "weaknesses": ["..."],
    "suggestions": ["..."],
    "decision": "accept" | "improve" | "reject",
    "improvement_instructions": "..."
}}"""


def get_language_config(language: str) -> Dict[str, Any]:
    """
    Función helper para obtener configuración de idioma.
    
    Args:
        language: Código de idioma
        
    Returns:
        Configuración completa del idioma
    """
    return {
        "code": language,
        "name": LanguageSupport.get_language_name(language),
        "tts_config": LanguageSupport.get_tts_config(language),
        "system_prompts": {
            agent: LanguageSupport.get_system_prompt(language, agent)
            for agent in ["planner", "generator", "evaluator"]
        },
    }
