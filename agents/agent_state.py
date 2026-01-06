"""
Definición del estado compartido para el workflow de generación de contenido.
"""

from typing import TypedDict, List, Dict, Optional, Any


class ContentGenerationState(TypedDict):
    """Estado compartido entre todos los agentes del workflow."""
    
    # Input inicial
    topic: str
    language: str
    
    # Plan generado por el planificador
    plan: Optional[Dict[str, Any]]
    
    # Contenido generado por cada agente generador
    content_v1: Optional[List[Dict[str, Any]]]  # Contenido del generador 1
    content_v2: Optional[List[Dict[str, Any]]]  # Contenido del generador 2
    
    # Evaluación y feedback
    evaluation: Optional[Dict[str, Any]]
    feedback_history: List[Dict[str, Any]]
    
    # Control del workflow
    iteration_count: int
    max_iterations: int
    quality_threshold: float
    
    # Output final
    final_content: Optional[List[Dict[str, Any]]]
    
    # Metadata
    metadata: Dict[str, Any]
