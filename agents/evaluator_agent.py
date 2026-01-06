"""
Agente evaluador que evalúa la calidad del contenido generado.
"""

import json
from typing import Dict, Any, List, Optional
from agents.agent_state import ContentGenerationState
from utils.llm_client import LLMClient, create_llm_client_for_agent
from utils.language_support import LanguageSupport, Language
from utils.rich_logger import get_logger


class EvaluatorAgent:
    """Agente responsable de evaluar la calidad del contenido generado."""
    
    def __init__(self, llm_client: LLMClient = None):
        """
        Inicializa el agente evaluador.
        
        Args:
            llm_client: Cliente LLM (si no se proporciona, se crea uno)
        """
        self.llm_client = llm_client or create_llm_client_for_agent("evaluator")
    
    def evaluate(self, state: ContentGenerationState) -> Dict[str, Any]:
        """
        Evalúa el contenido generado por ambos generadores.
        
        Args:
            state: Estado actual del workflow
            
        Returns:
            Estado actualizado con la evaluación
        """
        logger = get_logger()
        
        content_v1 = state.get("content_v1")
        content_v2 = state.get("content_v2")
        language = state["language"]
        quality_threshold = state.get("quality_threshold", 70.0)
        iteration_count = state.get("iteration_count", 0)
        
        logger.agent_start("Evaluator", f"Evaluando contenido generado (Iteración {iteration_count + 1})")
        logger.info(f"Umbral de calidad: {quality_threshold}/100")
        
        if not content_v1 and not content_v2:
            logger.error("No hay contenido para evaluar")
            raise ValueError("No hay contenido para evaluar.")
        
        # Contar contenido disponible
        v1_chapters = len(content_v1) if content_v1 else 0
        v2_chapters = len(content_v2) if content_v2 else 0
        logger.info(f"Contenido a evaluar: Generator-1: {v1_chapters} capítulos, Generator-2: {v2_chapters} capítulos")
        
        # Obtener prompts según el idioma
        system_prompt = LanguageSupport.get_system_prompt(language, "evaluator")
        evaluation_prompt = self._build_evaluation_prompt(
            content_v1=content_v1,
            content_v2=content_v2,
            language=language,
        )
        
        logger.debug("Enviando contenido al LLM para evaluación...")
        
        # Generar evaluación usando el LLM
        response = self.llm_client.generate(
            prompt=evaluation_prompt,
            system_prompt=system_prompt,
            temperature=0.3,  # Menos creatividad para evaluación
        )
        
        # Parsear respuesta
        evaluation = self._parse_evaluation_response(response)
        
        # Determinar si se necesita mejorar
        overall_score = evaluation.get("overall_score", 0)
        if overall_score < quality_threshold and state.get("iteration_count", 0) < state.get("max_iterations", 3):
            evaluation["decision"] = "improve"
        elif overall_score >= quality_threshold:
            evaluation["decision"] = "accept"
        else:
            evaluation["decision"] = "reject"
        
        # Log de resultados de evaluación
        decision = evaluation["decision"]
        decision_emoji = {"accept": "✅", "improve": "🔄", "reject": "❌"}.get(decision, "❓")
        decision_color = {"accept": "ACEPTADO", "improve": "NECESITA MEJORAS", "reject": "RECHAZADO"}.get(decision, decision)
        
        logger.section("🔍 Resultados de Evaluación")
        
        # Mostrar puntuación con barra visual
        score_bar_length = 20
        score_filled = int(score_bar_length * overall_score / 100)
        score_bar = "█" * score_filled + "░" * (score_bar_length - score_filled)
        logger.info(f"Puntuación: [{score_bar}] {overall_score}/100")
        logger.info(f"Decisión: {decision_emoji} {decision_color}")
        
        # Mostrar fortalezas y debilidades
        strengths = evaluation.get("strengths", [])
        weaknesses = evaluation.get("weaknesses", [])
        
        if strengths:
            logger.success("Fortalezas:")
            for s in strengths[:3]:  # Limitar a 3
                logger.info(f"  ✓ {s}")
        
        if weaknesses:
            logger.warning("Áreas de mejora:")
            for w in weaknesses[:3]:  # Limitar a 3
                logger.info(f"  ✗ {w}")
        
        if decision == "improve" and evaluation.get("improvement_instructions"):
            logger.info(f"Instrucciones de mejora: {evaluation.get('improvement_instructions', '')[:200]}...")
        
        logger.agent_complete("Evaluator", f"Puntuación: {overall_score}/100 - {decision_color}")
        
        # Actualizar estado
        state["evaluation"] = evaluation
        
        # Agregar a historial de feedback
        feedback_entry = {
            "iteration": state.get("iteration_count", 0),
            "overall_score": overall_score,
            "decision": evaluation["decision"],
            "improvement_instructions": evaluation.get("improvement_instructions", ""),
            "scores_by_chapter": evaluation.get("scores_by_chapter", []),
        }
        state["feedback_history"] = state.get("feedback_history", [])
        state["feedback_history"].append(feedback_entry)
        
        return state
    
    def _build_evaluation_prompt(
        self,
        content_v1: Optional[List[Dict[str, Any]]],
        content_v2: Optional[List[Dict[str, Any]]],
        language: str,
    ) -> str:
        """
        Construye el prompt de evaluación.
        
        Args:
            content_v1: Contenido del generador 1
            content_v2: Contenido del generador 2
            language: Idioma
            
        Returns:
            Prompt completo para evaluación
        """
        if language == Language.SPANISH or language == "es":
            prompt = """Evalúa la calidad del siguiente contenido generado para un audiobook.

Criterios de evaluación:
1. Claridad y comprensibilidad (0-25 puntos)
2. Estructura y organización (0-25 puntos)
3. Completitud del tema (0-25 puntos)
4. Apropiado para formato audiobook (0-15 puntos)
5. Calidad de escritura (0-10 puntos)

"""
        else:  # English
            prompt = """Evaluate the quality of the following generated content for an audiobook.

Evaluation criteria:
1. Clarity and comprehensibility (0-25 points)
2. Structure and organization (0-25 points)
3. Topic completeness (0-25 points)
4. Appropriate for audiobook format (0-15 points)
5. Writing quality (0-10 points)

"""
        
        # Agregar contenido del generador 1
        if content_v1:
            prompt += "\n=== CONTENIDO DEL GENERADOR 1 ===\n"
            for chapter in content_v1:
                prompt += f"\n--- Capítulo {chapter.get('chapter_number', '?')}: {chapter.get('chapter_title', '')} ---\n"
                prompt += chapter.get("content", "")[:2000] + "...\n"  # Limitar longitud
        
        # Agregar contenido del generador 2
        if content_v2:
            prompt += "\n=== CONTENIDO DEL GENERADOR 2 ===\n"
            for chapter in content_v2:
                prompt += f"\n--- Capítulo {chapter.get('chapter_number', '?')}: {chapter.get('chapter_title', '')} ---\n"
                prompt += chapter.get("content", "")[:2000] + "...\n"  # Limitar longitud
        
        # Agregar instrucciones de formato
        eval_format_prompt = LanguageSupport.get_evaluation_prompt(language)
        prompt += f"\n\n{eval_format_prompt}"
        
        return prompt
    
    def _parse_evaluation_response(self, response: str) -> Dict[str, Any]:
        """
        Parsea la respuesta del LLM a un diccionario de evaluación.
        
        Args:
            response: Respuesta del LLM
            
        Returns:
            Evaluación estructurada
        """
        try:
            # Buscar JSON en la respuesta
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                evaluation = json.loads(json_str)
                
                # Validar estructura básica
                if "overall_score" in evaluation:
                    return evaluation
        except json.JSONDecodeError:
            pass
        
        # Si falla el parsing, crear evaluación por defecto
        return {
            "overall_score": 50,
            "scores_by_chapter": [],
            "strengths": ["Contenido generado"],
            "weaknesses": ["No se pudo evaluar completamente"],
            "suggestions": ["Revisar manualmente"],
            "decision": "improve",
            "improvement_instructions": "Mejorar la estructura y claridad del contenido",
        }
