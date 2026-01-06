"""
Agente planificador que crea la estructura de contenido basada en el tema.
"""

import json
from typing import Dict, Any
from agents.agent_state import ContentGenerationState
from utils.llm_client import LLMClient, create_llm_client_for_agent
from utils.language_support import LanguageSupport
from utils.rich_logger import get_logger


class PlannerAgent:
    """Agente responsable de planificar la estructura del contenido."""
    
    def __init__(self, llm_client: LLMClient = None):
        """
        Inicializa el agente planificador.
        
        Args:
            llm_client: Cliente LLM (si no se proporciona, se crea uno)
        """
        self.llm_client = llm_client or create_llm_client_for_agent("planner")
    
    def plan(self, state: ContentGenerationState) -> Dict[str, Any]:
        """
        Genera un plan de contenido basado en el tema.
        
        Args:
            state: Estado actual del workflow
            
        Returns:
            Estado actualizado con el plan generado
        """
        logger = get_logger()
        
        topic = state["topic"]
        language = state["language"]
        
        logger.agent_start("Planner", f"Planificando estructura para tema: {topic}")
        logger.info(f"Idioma seleccionado: {language}")
        
        # Obtener prompts según el idioma
        system_prompt = LanguageSupport.get_system_prompt(language, "planner")
        user_prompt = LanguageSupport.get_planning_prompt(language, topic)
        
        logger.debug("Enviando solicitud de planificación al LLM...")
        
        # Generar plan usando el LLM
        response = self.llm_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
        )
        
        # Parsear respuesta JSON
        plan = self._parse_plan_response(response)
        
        # Log del plan generado
        num_chapters = len(plan.get("chapters", []))
        chapter_titles = [ch.get("title", "Sin título") for ch in plan.get("chapters", [])]
        
        logger.agent_complete("Planner", f"Plan creado con {num_chapters} capítulo(s)")
        logger.section("📋 Estructura del Plan")
        
        # Mostrar tabla de capítulos
        headers = ["#", "Título", "Temas", "Palabras Est."]
        rows = []
        for ch in plan.get("chapters", []):
            topics_count = len(ch.get("topics", []))
            rows.append([
                ch.get("number", "?"),
                ch.get("title", "Sin título")[:30],
                f"{topics_count} tema(s)",
                ch.get("estimated_length", "?")
            ])
        logger.table(headers, rows)
        
        # Actualizar estado
        state["plan"] = plan
        state["metadata"] = state.get("metadata", {})
        state["metadata"]["planning_completed"] = True
        
        return state
    
    def _parse_plan_response(self, response: str) -> Dict[str, Any]:
        """
        Parsea la respuesta del LLM a un diccionario de plan.
        
        Args:
            response: Respuesta del LLM
            
        Returns:
            Plan estructurado
        """
        # Intentar extraer JSON de la respuesta
        try:
            # Buscar JSON en la respuesta (puede tener texto antes/después)
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                plan = json.loads(json_str)
                
                # Validar estructura básica
                if "chapters" in plan and isinstance(plan["chapters"], list):
                    return plan
        except json.JSONDecodeError:
            pass
        
        # Si falla el parsing, crear un plan básico
        return {
            "chapters": [
                {
                    "number": 1,
                    "title": "Introducción",
                    "topics": ["Introducción al tema"],
                    "estimated_length": 1000,
                }
            ],
            "total_estimated_length": 1000,
        }
