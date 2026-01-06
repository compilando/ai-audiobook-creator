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
        size = state.get("size", "medium")
        
        logger.agent_start("Planner", f"Planificando: {topic[:50]}...")
        
        # Obtener prompts según el idioma y tamaño
        system_prompt = LanguageSupport.get_system_prompt(language, "planner")
        user_prompt = LanguageSupport.get_planning_prompt(language, topic, size)
        
        # Generar plan usando el LLM
        response = self.llm_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
        )
        
        # Parsear respuesta JSON (pasar estado para configuración de tamaño)
        plan = self._parse_plan_response(response, state)
        
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
        
        # Enviar plan completo para streaming a Gradio
        if hasattr(logger, 'plan_generated'):
            logger.plan_generated(plan)
        
        # Actualizar estado
        state["plan"] = plan
        state["metadata"] = state.get("metadata", {})
        state["metadata"]["planning_completed"] = True
        
        return state
    
    def _parse_plan_response(self, response: str, state: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Parsea la respuesta del LLM a un diccionario de plan.
        
        Args:
            response: Respuesta del LLM
            state: Estado actual con configuración de tamaño (opcional)
            
        Returns:
            Plan estructurado
        """
        from utils.language_support import LanguageSupport
        
        # Obtener configuración de tamaño del estado
        size = state.get("size", "medium") if state else "medium"
        size_config = LanguageSupport.get_size_config(size)
        
        # Intentar extraer JSON de la respuesta
        try:
            # Buscar JSON en la respuesta (puede tener texto antes/después)
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                
                # Intentar corregir errores comunes de JSON
                # Eliminar texto después del último ] válido dentro de "chapters"
                import re
                # Buscar el array de chapters
                chapters_match = re.search(r'"chapters"\s*:\s*\[', json_str)
                if chapters_match:
                    # Encontrar todos los objetos de capítulo válidos
                    chapter_pattern = r'\{\s*"number"\s*:\s*\d+\s*,\s*"title"\s*:\s*"[^"]*"\s*,\s*"topics"\s*:\s*\[[^\]]*\]\s*,\s*"estimated_length"\s*:\s*\d+\s*\}'
                    chapters = re.findall(chapter_pattern, json_str)
                    
                    if chapters:
                        # Reconstruir JSON válido
                        chapters_json = "[" + ",".join(chapters) + "]"
                        total_length = sum(
                            int(re.search(r'"estimated_length"\s*:\s*(\d+)', ch).group(1))
                            for ch in chapters
                        )
                        plan = {
                            "chapters": json.loads(chapters_json),
                            "total_estimated_length": total_length
                        }
                        
                        # Validar que tiene suficientes capítulos
                        if len(plan["chapters"]) >= size_config["chapters_min"]:
                            return plan
                
                # Intentar parsing normal
                plan = json.loads(json_str)
                
                # Validar estructura básica
                if "chapters" in plan and isinstance(plan["chapters"], list) and len(plan["chapters"]) > 0:
                    return plan
                    
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # Si falla el parsing, crear un plan completo según el tamaño
        logger = get_logger()
        logger.warning(f"JSON de plan inválido, generando plan de fallback con {size_config['chapters_max']} capítulos")
        
        topic = state.get("topic", "tema general") if state else "tema general"
        language = state.get("language", "es") if state else "es"
        
        # Generar plan de fallback completo
        if language == "es":
            chapter_titles = [
                ("Introducción y Contexto", ["panorama general", "importancia del tema", "objetivos de aprendizaje"]),
                ("Orígenes e Historia", ["antecedentes históricos", "evolución inicial", "eventos clave"]),
                ("Desarrollo y Crecimiento", ["período de expansión", "hitos importantes", "cambios significativos"]),
                ("Características Principales", ["elementos distintivos", "aspectos técnicos", "ejemplos relevantes"]),
                ("Impacto y Legado", ["influencia cultural", "repercusiones actuales", "aplicaciones prácticas"]),
                ("Conclusiones y Reflexiones", ["resumen de lo aprendido", "perspectivas futuras", "cierre inspirador"]),
            ]
        else:
            chapter_titles = [
                ("Introduction and Context", ["general overview", "topic importance", "learning objectives"]),
                ("Origins and History", ["historical background", "early evolution", "key events"]),
                ("Development and Growth", ["expansion period", "important milestones", "significant changes"]),
                ("Main Characteristics", ["distinctive elements", "technical aspects", "relevant examples"]),
                ("Impact and Legacy", ["cultural influence", "current repercussions", "practical applications"]),
                ("Conclusions and Reflections", ["summary of lessons", "future perspectives", "inspiring close"]),
            ]
        
        # Ajustar cantidad de capítulos según el tamaño
        num_chapters = size_config["chapters_max"]
        words_per_chapter = size_config["words_per_chapter"]
        
        chapters = []
        for i, (title, topics) in enumerate(chapter_titles[:num_chapters], 1):
            chapters.append({
                "number": i,
                "title": title,
                "topics": topics,
                "estimated_length": words_per_chapter,
            })
        
        return {
            "chapters": chapters,
            "total_estimated_length": words_per_chapter * num_chapters,
        }
