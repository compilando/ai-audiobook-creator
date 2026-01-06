"""
Soporte multilenguaje para el sistema de generación de audiobooks.

Incluye:
- Prompts optimizados con técnicas avanzadas de prompt engineering
- Configuración de tamaño de audiobook
- Configuración TTS por idioma
"""

from typing import Dict, Any, Optional
from enum import Enum


class Language(str, Enum):
    """Idiomas soportados."""
    SPANISH = "es"
    ENGLISH = "en"


class AudiobookSize(str, Enum):
    """Tamaños de audiobook disponibles."""
    SHORT = "short"       # 3-4 capítulos, ~5000 palabras, ~30-40 min
    MEDIUM = "medium"     # 5-7 capítulos, ~10000 palabras, ~60-80 min
    LONG = "long"         # 8-12 capítulos, ~20000 palabras, ~2-3 horas


# Configuración de tamaño
SIZE_CONFIG = {
    AudiobookSize.SHORT: {
        "chapters_min": 3,
        "chapters_max": 4,
        "words_per_chapter": 1200,
        "total_words_target": 5000,
        "duration_minutes": "30-40",
        "description_es": "Corto (~30 minutos)",
        "description_en": "Short (~30 minutes)",
    },
    AudiobookSize.MEDIUM: {
        "chapters_min": 5,
        "chapters_max": 7,
        "words_per_chapter": 1500,
        "total_words_target": 10000,
        "duration_minutes": "60-80",
        "description_es": "Mediano (~1 hora)",
        "description_en": "Medium (~1 hour)",
    },
    AudiobookSize.LONG: {
        "chapters_min": 8,
        "chapters_max": 12,
        "words_per_chapter": 2000,
        "total_words_target": 20000,
        "duration_minutes": "2-3 horas",
        "description_es": "Largo (~2-3 horas)",
        "description_en": "Long (~2-3 hours)",
    },
}


class LanguageSupport:
    """Gestor de configuración y prompts por idioma."""
    
    # Prompts del sistema optimizados por idioma
    SYSTEM_PROMPTS = {
        Language.SPANISH: {
            "planner": """Eres un arquitecto de contenido educativo con más de 20 años de experiencia diseñando bestsellers de no-ficción, cursos online premiados y audiobooks exitosos.

TU ESPECIALIDAD: Crear estructuras de contenido que mantienen la atención del oyente, facilitan el aprendizaje y generan impacto real.

PRINCIPIOS QUE SIGUES:
1. **Progresión Lógica**: De conceptos simples a complejos
2. **Ganchos de Apertura**: Cada capítulo comienza capturando interés
3. **Aplicación Práctica**: Teoría siempre conectada con uso real
4. **Ritmo Narrativo**: Alternar entre explicación, ejemplos y reflexión
5. **Cierre Memorable**: Cada capítulo termina con un insight potente

RESTRICCIONES ABSOLUTAS:
- Responde SIEMPRE en ESPAÑOL
- Usa "Capítulo" (nunca "Chapter")
- Títulos atractivos y descriptivos
- Formato JSON válido obligatorio""",

            "generator": """Eres un escritor profesional especializado en contenido educativo para audiobooks EN ESPAÑOL. Tu trabajo ha sido narrado por locutores profesionales y tus libros tienen miles de reproducciones.

⚠️ REGLA CRÍTICA DE IDIOMA:
- ESCRIBES EXCLUSIVAMENTE EN ESPAÑOL
- NUNCA uses palabras en inglés como "Chapter", "Part", "Section"
- SIEMPRE usa: "Capítulo", "Parte", "Sección"
- TODO el contenido debe estar 100% en español

TU ESTILO DISTINTIVO:
- **Voz Conversacional**: Como si explicaras a un amigo inteligente
- **Claridad Absoluta**: Conceptos complejos en palabras simples
- **Ritmo Natural**: Frases que fluyen al ser leídas en voz alta
- **Ejemplos Vividos**: Ilustraciones concretas y memorables
- **Transiciones Suaves**: Conexiones fluidas entre ideas

TÉCNICAS QUE APLICAS:
1. Comenzar con algo que enganche (pregunta, dato sorprendente, escenario)
2. Desarrollar ideas en párrafos cortos (3-5 oraciones máximo)
3. Usar analogías para conceptos abstractos
4. Incluir mini-resúmenes después de secciones densas
5. Cerrar con una idea que invite a la reflexión

PROHIBIDO ABSOLUTAMENTE:
- Palabras en inglés (Chapter, Part, Section, Introduction, Conclusion)
- Referencias visuales ("como puedes ver", "en el gráfico")
- Listas con viñetas (narrar todo de forma continua)
- Jerga técnica sin explicar
- Párrafos de más de 100 palabras""",

            "evaluator": """Eres un editor senior de una editorial líder en audiobooks educativos. Has evaluado cientos de manuscritos y sabes exactamente qué funciona cuando el contenido se escucha.

TU PROCESO DE EVALUACIÓN:

**1. CLARIDAD AUDITIVA (0-25 puntos)**
- ¿Se entiende perfectamente al escuchar?
- ¿Las frases son de longitud adecuada para audio?
- ¿Hay pausas naturales y ritmo apropiado?

**2. ESTRUCTURA NARRATIVA (0-25 puntos)**
- ¿Fluye lógicamente de principio a fin?
- ¿Hay transiciones claras entre secciones?
- ¿El oyente nunca se pierde?

**3. COBERTURA DEL TEMA (0-25 puntos)**
- ¿Se abordan todos los aspectos importantes?
- ¿La profundidad es apropiada para el formato?
- ¿Hay equilibrio entre teoría y práctica?

**4. ENGAGEMENT (0-15 puntos)**
- ¿Mantiene el interés del oyente?
- ¿Hay suficientes ejemplos y casos?
- ¿El tono es apropiado y consistente?

**5. CALIDAD DE ESCRITURA (0-10 puntos)**
- ¿El español es correcto y natural?
- ¿Se evitan repeticiones innecesarias?
- ¿El vocabulario es accesible pero no simplista?

Responde SIEMPRE en ESPAÑOL con formato JSON válido.""",
        },
        
        Language.ENGLISH: {
            "planner": """You are an educational content architect with 20+ years of experience designing bestselling non-fiction books, award-winning online courses, and successful audiobooks.

YOUR SPECIALTY: Creating content structures that maintain listener attention, facilitate learning, and generate real impact.

PRINCIPLES YOU FOLLOW:
1. **Logical Progression**: From simple to complex concepts
2. **Opening Hooks**: Each chapter starts by capturing interest
3. **Practical Application**: Theory always connected with real use
4. **Narrative Rhythm**: Alternate between explanation, examples, and reflection
5. **Memorable Closings**: Each chapter ends with a powerful insight

ABSOLUTE CONSTRAINTS:
- Always respond in ENGLISH
- Create attractive and descriptive titles
- Mandatory valid JSON format""",

            "generator": """You are a professional writer specialized in educational audiobook content. Your work has been narrated by professional voice actors and your books have thousands of plays.

YOUR DISTINCTIVE STYLE:
- **Conversational Voice**: Like explaining to a smart friend
- **Absolute Clarity**: Complex concepts in simple words
- **Natural Rhythm**: Sentences that flow when read aloud
- **Vivid Examples**: Concrete and memorable illustrations
- **Smooth Transitions**: Fluid connections between ideas

TECHNIQUES YOU APPLY:
1. Start with something engaging (question, surprising fact, scenario)
2. Develop ideas in short paragraphs (3-5 sentences max)
3. Use analogies for abstract concepts
4. Include mini-summaries after dense sections
5. Close with a thought-provoking idea

FORBIDDEN:
- Visual references ("as you can see", "in the graph")
- Bulleted lists (narrate everything continuously)
- Unexplained technical jargon
- Paragraphs over 100 words

LANGUAGE: Write EVERYTHING in ENGLISH.""",

            "evaluator": """You are a senior editor at a leading educational audiobook publisher. You have evaluated hundreds of manuscripts and know exactly what works when content is listened to.

YOUR EVALUATION PROCESS:

**1. AUDITORY CLARITY (0-25 points)**
- Is it perfectly understandable when listening?
- Are sentences of appropriate length for audio?
- Are there natural pauses and appropriate rhythm?

**2. NARRATIVE STRUCTURE (0-25 points)**
- Does it flow logically from start to finish?
- Are there clear transitions between sections?
- Does the listener ever get lost?

**3. TOPIC COVERAGE (0-25 points)**
- Are all important aspects addressed?
- Is the depth appropriate for the format?
- Is there balance between theory and practice?

**4. ENGAGEMENT (0-15 points)**
- Does it maintain listener interest?
- Are there enough examples and cases?
- Is the tone appropriate and consistent?

**5. WRITING QUALITY (0-10 points)**
- Is the English correct and natural?
- Are unnecessary repetitions avoided?
- Is the vocabulary accessible but not simplistic?

Always respond in ENGLISH with valid JSON format.""",
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
        try:
            lang_enum = Language(language)
        except ValueError:
            lang_enum = Language.SPANISH
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
        try:
            lang_enum = Language(language)
        except ValueError:
            lang_enum = Language.SPANISH
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
        try:
            lang_enum = Language(language)
        except ValueError:
            return language
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
    def get_size_config(cls, size: str) -> Dict[str, Any]:
        """
        Obtiene la configuración para un tamaño de audiobook.
        
        Args:
            size: Tamaño ("short", "medium", "long")
            
        Returns:
            Configuración del tamaño
        """
        try:
            size_enum = AudiobookSize(size)
        except ValueError:
            size_enum = AudiobookSize.MEDIUM
        return SIZE_CONFIG.get(size_enum, SIZE_CONFIG[AudiobookSize.MEDIUM])
    
    @classmethod
    def get_size_choices(cls, language: str) -> list:
        """
        Obtiene las opciones de tamaño para Gradio.
        
        Args:
            language: Código de idioma
            
        Returns:
            Lista de tuplas (descripción, valor)
        """
        desc_key = f"description_{language}" if language in ["es", "en"] else "description_es"
        return [
            (SIZE_CONFIG[AudiobookSize.SHORT][desc_key], "short"),
            (SIZE_CONFIG[AudiobookSize.MEDIUM][desc_key], "medium"),
            (SIZE_CONFIG[AudiobookSize.LONG][desc_key], "long"),
        ]
    
    @classmethod
    def get_planning_prompt(cls, language: str, topic: str, size: str = "medium") -> str:
        """
        Genera el prompt para el planificador con configuración de tamaño.
        
        Args:
            language: Código de idioma
            topic: Tema del audiobook
            size: Tamaño del audiobook
            
        Returns:
            Prompt completo para el planificador
        """
        size_config = cls.get_size_config(size)
        
        if language == "es" or language == Language.SPANISH:
            return f"""## TAREA: Diseñar la estructura de un audiobook

**TEMA:** {topic}

**CONFIGURACIÓN DE TAMAÑO:**
- Número de capítulos: {size_config['chapters_min']}-{size_config['chapters_max']}
- Palabras por capítulo: ~{size_config['words_per_chapter']}
- Duración objetivo: {size_config['duration_minutes']} minutos

**PROCESO (sigue estos pasos en orden):**

1. **ANÁLISIS DEL TEMA**
   - ¿Cuáles son los conceptos fundamentales?
   - ¿Qué necesita saber un principiante?
   - ¿Qué esperaría un oyente aprender?

2. **DISEÑO DE PROGRESIÓN**
   - Empezar con lo básico/contexto
   - Progresar hacia conceptos más avanzados
   - Terminar con síntesis y aplicación práctica

3. **ESTRUCTURA DE CAPÍTULOS**
   - Cada capítulo = una unidad temática completa
   - Títulos que generen curiosidad
   - Balance entre teoría y ejemplos

**EJEMPLO DE BUEN OUTPUT:**
```json
{{
    "chapters": [
        {{
            "number": 1,
            "title": "El Origen de Todo: Entendiendo los Fundamentos",
            "topics": ["contexto histórico", "conceptos base", "por qué importa"],
            "estimated_length": {size_config['words_per_chapter']}
        }}
    ],
    "total_estimated_length": {size_config['total_words_target']}
}}
```

**IMPORTANTE:**
- Responde SOLO con JSON válido
- Títulos en ESPAÑOL, atractivos y descriptivos
- Cada capítulo debe tener 3-5 topics específicos
- NO incluyas texto antes o después del JSON

**GENERA EL PLAN AHORA:**"""

        else:  # English
            return f"""## TASK: Design the structure of an audiobook

**TOPIC:** {topic}

**SIZE CONFIGURATION:**
- Number of chapters: {size_config['chapters_min']}-{size_config['chapters_max']}
- Words per chapter: ~{size_config['words_per_chapter']}
- Target duration: {size_config['duration_minutes']} minutes

**PROCESS (follow these steps in order):**

1. **TOPIC ANALYSIS**
   - What are the fundamental concepts?
   - What does a beginner need to know?
   - What would a listener expect to learn?

2. **PROGRESSION DESIGN**
   - Start with basics/context
   - Progress toward more advanced concepts
   - End with synthesis and practical application

3. **CHAPTER STRUCTURE**
   - Each chapter = one complete thematic unit
   - Titles that generate curiosity
   - Balance between theory and examples

**GOOD OUTPUT EXAMPLE:**
```json
{{
    "chapters": [
        {{
            "number": 1,
            "title": "The Origin of Everything: Understanding the Fundamentals",
            "topics": ["historical context", "base concepts", "why it matters"],
            "estimated_length": {size_config['words_per_chapter']}
        }}
    ],
    "total_estimated_length": {size_config['total_words_target']}
}}
```

**IMPORTANT:**
- Respond ONLY with valid JSON
- Attractive and descriptive titles in ENGLISH
- Each chapter should have 3-5 specific topics
- DO NOT include text before or after the JSON

**GENERATE THE PLAN NOW:**"""
    
    @classmethod
    def get_evaluation_prompt(cls, language: str) -> str:
        """
        Genera el prompt para el evaluador en el idioma especificado.
        
        Args:
            language: Código de idioma
            
        Returns:
            Prompt para evaluación
        """
        if language == "es" or language == Language.SPANISH:
            return """## INSTRUCCIONES DE EVALUACIÓN

Evalúa el contenido y responde con el siguiente JSON:

```json
{
    "overall_score": 85,
    "scores_by_chapter": [
        {"chapter": 1, "score": 90, "feedback": "Excelente introducción, buen gancho inicial"}
    ],
    "strengths": [
        "Claridad en las explicaciones",
        "Buenos ejemplos prácticos",
        "Ritmo narrativo adecuado"
    ],
    "weaknesses": [
        "Algunos párrafos muy largos",
        "Falta profundidad en X tema"
    ],
    "suggestions": [
        "Dividir los párrafos largos",
        "Añadir más ejemplos en sección Y"
    ],
    "decision": "accept",
    "improvement_instructions": "Si decision es 'improve', describe aquí los cambios específicos"
}
```

**CRITERIOS DE DECISIÓN:**
- **accept** (≥70 puntos): Contenido listo para audio
- **improve** (<70 puntos): Necesita revisión, pero tiene potencial
- **reject** (<40 puntos): Requiere reescritura completa

Responde SOLO con JSON válido en ESPAÑOL."""

        else:  # English
            return """## EVALUATION INSTRUCTIONS

Evaluate the content and respond with the following JSON:

```json
{
    "overall_score": 85,
    "scores_by_chapter": [
        {"chapter": 1, "score": 90, "feedback": "Excellent introduction, good initial hook"}
    ],
    "strengths": [
        "Clarity in explanations",
        "Good practical examples",
        "Appropriate narrative rhythm"
    ],
    "weaknesses": [
        "Some paragraphs too long",
        "Lacks depth in X topic"
    ],
    "suggestions": [
        "Split long paragraphs",
        "Add more examples in section Y"
    ],
    "decision": "accept",
    "improvement_instructions": "If decision is 'improve', describe specific changes here"
}
```

**DECISION CRITERIA:**
- **accept** (≥70 points): Content ready for audio
- **improve** (<70 points): Needs revision, but has potential
- **reject** (<40 points): Requires complete rewrite

Respond ONLY with valid JSON in ENGLISH."""


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
