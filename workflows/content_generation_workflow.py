"""
Workflow LangGraph para orquestación del sistema multiagente de generación de contenido.
"""

from typing import Dict, Any, Literal, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage

from agents.agent_state import ContentGenerationState
from agents.planner_agent import PlannerAgent
from agents.content_generator_agent import ContentGeneratorAgent
from agents.evaluator_agent import EvaluatorAgent
from integration.content_formatter import ContentFormatter
from utils.rich_logger import get_logger


def create_content_generation_workflow() -> StateGraph:
    """
    Crea el workflow LangGraph para generación de contenido.
    
    Returns:
        Grafo de estado configurado
    """
    # Inicializar agentes
    planner = PlannerAgent()
    generator1 = ContentGeneratorAgent(agent_id="generator1")
    generator2 = ContentGeneratorAgent(agent_id="generator2")
    evaluator = EvaluatorAgent()
    formatter = ContentFormatter()
    
    # Crear grafo de estado usando TypedDict
    workflow = StateGraph(ContentGenerationState)
    
    # Agregar nodos
    workflow.add_node("planner", planner_node(planner))
    workflow.add_node("generator1", generator1_node(generator1))
    workflow.add_node("generator2", generator2_node(generator2))
    workflow.add_node("evaluator", evaluator_node(evaluator))
    workflow.add_node("merge", merge_node(formatter))
    workflow.add_node("format", format_node(formatter))
    
    # Definir flujo
    workflow.set_entry_point("planner")
    
    # Después de planificar, generar contenido
    # Nota: LangGraph ejecuta nodos conectados secuencialmente
    # Para paralelismo real, se ejecutarían en diferentes threads/processes
    workflow.add_edge("planner", "generator1")
    workflow.add_edge("generator1", "generator2")
    workflow.add_edge("generator2", "evaluator")
    
    # Después de evaluar, decidir si mejorar o continuar
    workflow.add_conditional_edges(
        "evaluator",
        should_improve,
        {
            "improve": "generator1",  # Volver a generar con feedback
            "accept": "merge",  # Fusionar y continuar
            "reject": END,  # Terminar (contenido rechazado)
        },
    )
    
    # Después de fusionar, formatear
    workflow.add_edge("merge", "format")
    
    # Después de formatear, terminar
    workflow.add_edge("format", END)
    
    return workflow.compile()


def planner_node(planner: PlannerAgent):
    """Nodo del planificador."""
    def _plan(state: ContentGenerationState) -> ContentGenerationState:
        logger = get_logger()
        logger.step("Planificación de contenido", 1, 6)
        try:
            return planner.plan(state)
        except Exception as e:
            logger.error(f"Error en nodo Planner: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            raise
    return _plan


def generator1_node(generator: ContentGeneratorAgent):
    """Nodo del generador 1."""
    def _generate(state: ContentGenerationState) -> ContentGenerationState:
        logger = get_logger()
        iteration = state.get("iteration_count", 0)
        logger.step(f"Generación de contenido (Generator-1) - Iteración {iteration + 1}", 2, 6)
        try:
            state["iteration_count"] = iteration
            return generator.generate(state)
        except Exception as e:
            logger.error(f"Error en nodo Generator-1: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            raise
    return _generate


def generator2_node(generator: ContentGeneratorAgent):
    """Nodo del generador 2."""
    def _generate(state: ContentGenerationState) -> ContentGenerationState:
        logger = get_logger()
        logger.step("Generación de contenido (Generator-2)", 3, 6)
        try:
            return generator.generate(state)
        except Exception as e:
            logger.error(f"Error en nodo Generator-2: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            raise
    return _generate


def evaluator_node(evaluator: EvaluatorAgent):
    """Nodo del evaluador."""
    def _evaluate(state: ContentGenerationState) -> ContentGenerationState:
        logger = get_logger()
        logger.step("Evaluación de calidad", 4, 6)
        try:
            state = evaluator.evaluate(state)
            state["iteration_count"] = state.get("iteration_count", 0) + 1
            return state
        except Exception as e:
            logger.error(f"Error en nodo Evaluator: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            raise
    return _evaluate


def merge_node(formatter: ContentFormatter):
    """Nodo que fusiona el mejor contenido."""
    def _merge(state: ContentGenerationState) -> ContentGenerationState:
        logger = get_logger()
        logger.step("Fusión del mejor contenido", 5, 6)
        
        try:
            content_v1 = state.get("content_v1")
            content_v2 = state.get("content_v2")
            evaluation = state.get("evaluation")
            
            logger.info("Combinando el mejor contenido de ambos generadores...")
            merged = formatter.merge_best_content(content_v1, content_v2, evaluation)
            state["final_content"] = merged
            
            # Log resumen del contenido fusionado
            if merged:
                if isinstance(merged, list):
                    # Es una lista de capítulos
                    total_words = sum(
                        len(ch.get("content", "").split()) 
                        for ch in merged 
                        if isinstance(ch, dict)
                    )
                    logger.success(f"Contenido fusionado: {len(merged)} capítulo(s), {total_words} palabras")
                elif isinstance(merged, dict):
                    full_text = merged.get("full_text", "")
                    word_count = len(full_text.split()) if full_text else 0
                    logger.success(f"Contenido fusionado: {word_count} palabras")
                else:
                    logger.success(f"Contenido fusionado: tipo {type(merged)}")
            else:
                logger.warning("No se generó contenido fusionado")
            
            return state
        except Exception as e:
            logger.error(f"Error en nodo Merge: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            raise
    return _merge


def format_node(formatter: ContentFormatter):
    """Nodo que formatea el contenido final."""
    def _format(state: ContentGenerationState) -> ContentGenerationState:
        logger = get_logger()
        logger.step("Formateo final del contenido", 6, 6)
        
        try:
            final_content = state.get("final_content")
            language = state.get("language", "es")
            
            if final_content:
                output_path = formatter.format_to_audiobook_text(
                    final_content, 
                    language=language
                )
                state["metadata"] = state.get("metadata", {})
                state["metadata"]["formatted_output_path"] = output_path
                logger.success(f"Contenido formateado guardado en: {output_path}")
            
            return state
        except Exception as e:
            logger.error(f"Error en nodo Format: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            raise
    return _format


def should_improve(state: ContentGenerationState) -> Literal["improve", "accept", "reject"]:
    """
    Decide si el contenido necesita mejoras.
    
    Args:
        state: Estado actual
        
    Returns:
        Decisión: "improve", "accept", o "reject"
    """
    evaluation = state.get("evaluation")
    if not evaluation:
        return "improve"
    
    decision = evaluation.get("decision", "improve")
    iteration_count = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 3)
    
    # Si ya se alcanzó el máximo de iteraciones, aceptar o rechazar
    if iteration_count >= max_iterations:
        if decision == "improve":
            return "accept"  # Aceptar aunque no sea perfecto
        return decision
    
    return decision
