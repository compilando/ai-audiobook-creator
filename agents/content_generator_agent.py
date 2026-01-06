"""
Agente generador de contenido que crea el texto completo para cada capítulo.
"""

from typing import Dict, Any, List, Optional
from agents.agent_state import ContentGenerationState
from utils.llm_client import LLMClient, create_llm_client_for_agent
from utils.language_support import LanguageSupport, Language
from utils.rich_logger import get_logger


class ContentGeneratorAgent:
    """Agente responsable de generar contenido textual completo."""
    
    def __init__(self, llm_client: LLMClient = None, agent_id: str = "generator1"):
        """
        Inicializa el agente generador.
        
        Args:
            llm_client: Cliente LLM (si no se proporciona, se crea uno)
            agent_id: Identificador del agente ("generator1" o "generator2")
        """
        self.agent_id = agent_id
        self.llm_client = llm_client or create_llm_client_for_agent(agent_id)
    
    def generate(self, state: ContentGenerationState) -> Dict[str, Any]:
        """
        Genera contenido para todos los capítulos del plan.
        
        Args:
            state: Estado actual del workflow
            
        Returns:
            Estado actualizado con el contenido generado
        """
        logger = get_logger()
        
        plan = state.get("plan")
        if not plan:
            logger.error("No hay plan disponible. Debe ejecutarse el planificador primero.")
            raise ValueError("No hay plan disponible. Debe ejecutarse el planificador primero.")
        
        language = state["language"]
        feedback_history = state.get("feedback_history", [])
        iteration_count = state.get("iteration_count", 0)
        
        # Identificar el agente con estilo
        agent_display = f"Generator-{self.agent_id[-1]}" if self.agent_id else "Generator"
        
        logger.agent_start(agent_display, f"Generando contenido para {len(plan.get('chapters', []))} capítulo(s)")
        
        if iteration_count > 0:
            logger.info(f"Iteración {iteration_count + 1} - Aplicando feedback previo")
        
        # Obtener prompts según el idioma
        system_prompt = LanguageSupport.get_system_prompt(language, "generator")
        
        # Si hay feedback, incluirlo en el prompt
        if feedback_history and iteration_count > 0:
            latest_feedback = feedback_history[-1]
            system_prompt += f"\n\nFeedback de la iteración anterior:\n{latest_feedback.get('improvement_instructions', '')}"
            logger.debug(f"Feedback aplicado: {latest_feedback.get('improvement_instructions', '')[:100]}...")
        
        # Generar contenido para cada capítulo
        chapters = plan.get("chapters", [])
        generated_content = []
        total_words = 0
        
        for i, chapter in enumerate(chapters, 1):
            chapter_title = chapter.get("title", "Sin título")
            logger.step(f"Generando capítulo {i}: {chapter_title}", i, len(chapters))
            
            chapter_content = self._generate_chapter_content(
                chapter=chapter,
                topic=state["topic"],
                language=language,
                system_prompt=system_prompt,
                feedback=feedback_history[-1] if feedback_history else None,
            )
            generated_content.append(chapter_content)
            
            word_count = chapter_content.get("word_count", 0)
            total_words += word_count
            logger.step_complete(f"Capítulo {i}", f"{word_count} palabras generadas")
        
        # Log resumen de generación
        logger.agent_complete(agent_display, f"Total: {total_words} palabras en {len(chapters)} capítulo(s)")
        
        # Mostrar resumen en tabla
        logger.section(f"📝 Resumen de Generación ({agent_display})")
        headers = ["Capítulo", "Título", "Palabras"]
        rows = [[
            ch.get("chapter_number", "?"),
            ch.get("chapter_title", "Sin título")[:25],
            ch.get("word_count", 0)
        ] for ch in generated_content]
        logger.table(headers, rows)
        
        # Actualizar estado según el ID del agente
        if self.agent_id == "generator1":
            state["content_v1"] = generated_content
        else:
            state["content_v2"] = generated_content
        
        return state
    
    def _generate_chapter_content(
        self,
        chapter: Dict[str, Any],
        topic: str,
        language: str,
        system_prompt: str,
        feedback: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Genera el contenido para un capítulo específico.
        
        Args:
            chapter: Información del capítulo
            topic: Tema principal
            language: Idioma
            system_prompt: Prompt del sistema
            feedback: Feedback de iteraciones anteriores (opcional)
            
        Returns:
            Contenido generado para el capítulo
        """
        chapter_num = chapter.get("number", 1)
        chapter_title = chapter.get("title", "")
        topics = chapter.get("topics", [])
        estimated_length = chapter.get("estimated_length", 1000)
        
        # Construir prompt del usuario
        if language == Language.SPANISH:
            user_prompt = f"""Escribe el contenido completo del Capítulo {chapter_num}: {chapter_title}

Tema principal del audiobook: {topic}

Temas a cubrir en este capítulo:
{chr(10).join(f"- {t}" for t in topics)}

Longitud estimada: aproximadamente {estimated_length} palabras

El contenido debe ser:
- Claro y fácil de entender cuando se escucha
- Bien estructurado con párrafos cortos
- Incluir ejemplos prácticos cuando sea apropiado
- Apropiado para formato audiobook (evitar referencias visuales)
- Progresivo y lógico

Escribe el contenido completo del capítulo:"""
        else:  # English
            user_prompt = f"""Write the complete content for Chapter {chapter_num}: {chapter_title}

Main topic of the audiobook: {topic}

Topics to cover in this chapter:
{chr(10).join(f"- {t}" for t in topics)}

Estimated length: approximately {estimated_length} words

The content must be:
- Clear and easy to understand when listening
- Well-structured with short paragraphs
- Include practical examples when appropriate
- Appropriate for audiobook format (avoid visual references)
- Progressive and logical

Write the complete chapter content:"""
        
        # Si hay feedback específico para este capítulo, incluirlo
        if feedback:
            chapter_feedback = next(
                (
                    item.get("feedback", "")
                    for item in feedback.get("scores_by_chapter", [])
                    if item.get("chapter") == chapter_num
                ),
                None,
            )
            if chapter_feedback:
                user_prompt += f"\n\nFeedback específico para este capítulo:\n{chapter_feedback}"
        
        # Generar contenido
        content = self.llm_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.8,  # Más creatividad para generación
        )
        
        return {
            "chapter_number": chapter_num,
            "chapter_title": chapter_title,
            "content": content,
            "word_count": len(content.split()),
            "agent_id": self.agent_id,
        }
