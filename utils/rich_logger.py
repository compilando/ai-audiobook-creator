"""
Sistema de logging rico y colorido para el generador de audiobooks.

Proporciona logging estructurado con colores y emojis para mejor visibilidad
durante el proceso de generación.
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import Optional, Any, Dict, Callable, List
from enum import Enum


class LogLevel(Enum):
    """Niveles de log con colores asociados."""
    DEBUG = ("DEBUG", "\033[90m", "🔍")      # Gris
    INFO = ("INFO", "\033[94m", "ℹ️")         # Azul
    SUCCESS = ("SUCCESS", "\033[92m", "✅")   # Verde
    WARNING = ("WARNING", "\033[93m", "⚠️")   # Amarillo
    ERROR = ("ERROR", "\033[91m", "❌")       # Rojo
    CRITICAL = ("CRITICAL", "\033[95m", "🚨") # Magenta
    STEP = ("STEP", "\033[96m", "📍")         # Cian
    AGENT = ("AGENT", "\033[95m", "🤖")       # Magenta
    LLM = ("LLM", "\033[93m", "🧠")           # Amarillo
    TTS = ("TTS", "\033[92m", "🎤")           # Verde
    AUDIO = ("AUDIO", "\033[94m", "🎧")       # Azul
    WORKFLOW = ("WORKFLOW", "\033[96m", "🔄") # Cian
    TIME = ("TIME", "\033[90m", "⏱️")         # Gris


class Colors:
    """Códigos de colores ANSI."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    
    # Colores de texto
    BLACK = "\033[30m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"
    
    # Colores de fondo
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"


class RichLogger:
    """
    Logger rico con colores y formato mejorado.
    
    Proporciona métodos específicos para cada tipo de evento
    durante la generación del audiobook.
    """
    
    def __init__(
        self,
        name: str = "audiobook",
        level: str = "INFO",
        show_timestamp: bool = True,
        show_elapsed: bool = True,
        use_colors: bool = True,
    ):
        """
        Inicializa el logger.
        
        Args:
            name: Nombre del logger
            level: Nivel de logging (DEBUG, INFO, WARNING, ERROR)
            show_timestamp: Mostrar timestamp en los mensajes
            show_elapsed: Mostrar tiempo transcurrido
            use_colors: Usar colores ANSI
        """
        self.name = name
        self.level = level
        self.show_timestamp = show_timestamp
        self.show_elapsed = show_elapsed
        self.use_colors = use_colors and self._supports_color()
        
        self.start_time = time.time()
        self.step_times: Dict[str, float] = {}
        
        # Configurar logging estándar también
        self._setup_standard_logging()
    
    def _supports_color(self) -> bool:
        """Verifica si la terminal soporta colores."""
        # Forzar colores si está en Docker o la variable está definida
        if os.environ.get("FORCE_COLOR") or os.environ.get("TERM"):
            return True
        return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
    
    def _setup_standard_logging(self):
        """Configura el logging estándar de Python."""
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(getattr(logging, self.level.upper(), logging.INFO))
        
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter('%(message)s'))
            self.logger.addHandler(handler)
    
    def _colorize(self, text: str, color: str) -> str:
        """Aplica color al texto si está habilitado."""
        if not self.use_colors:
            return text
        return f"{color}{text}{Colors.RESET}"
    
    def _format_time(self) -> str:
        """Formatea el timestamp actual."""
        now = datetime.now()
        return now.strftime("%H:%M:%S.%f")[:-3]
    
    def _format_elapsed(self) -> str:
        """Formatea el tiempo transcurrido."""
        elapsed = time.time() - self.start_time
        if elapsed < 60:
            return f"{elapsed:.2f}s"
        elif elapsed < 3600:
            mins = int(elapsed // 60)
            secs = elapsed % 60
            return f"{mins}m {secs:.1f}s"
        else:
            hours = int(elapsed // 3600)
            mins = int((elapsed % 3600) // 60)
            return f"{hours}h {mins}m"
    
    def _build_prefix(self, level: LogLevel) -> str:
        """Construye el prefijo del mensaje."""
        parts = []
        
        # Timestamp
        if self.show_timestamp:
            timestamp = self._format_time()
            parts.append(self._colorize(f"[{timestamp}]", Colors.GRAY))
        
        # Elapsed time
        if self.show_elapsed:
            elapsed = self._format_elapsed()
            parts.append(self._colorize(f"[+{elapsed}]", Colors.DIM))
        
        # Level con emoji y color
        level_name, color, emoji = level.value
        level_str = f"{emoji} {level_name}"
        parts.append(self._colorize(f"[{level_str}]", color))
        
        return " ".join(parts)
    
    def _log(self, level: LogLevel, message: str, **kwargs):
        """Log genérico con formato."""
        prefix = self._build_prefix(level)
        full_message = f"{prefix} {message}"
        
        # Agregar datos extra si existen
        if kwargs:
            details = " | ".join(f"{k}={v}" for k, v in kwargs.items())
            full_message += f" {self._colorize(f'({details})', Colors.DIM)}"
        
        print(full_message, flush=True)
    
    # ==================== Métodos de nivel ====================
    
    def debug(self, message: str, **kwargs):
        """Log de nivel DEBUG."""
        self._log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log de nivel INFO."""
        self._log(LogLevel.INFO, message, **kwargs)
    
    def success(self, message: str, **kwargs):
        """Log de éxito."""
        self._log(LogLevel.SUCCESS, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log de advertencia."""
        self._log(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log de error."""
        self._log(LogLevel.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log crítico."""
        self._log(LogLevel.CRITICAL, message, **kwargs)
    
    # ==================== Métodos específicos ====================
    
    def step(self, step_name: str, step_number: Optional[int] = None, total_steps: Optional[int] = None):
        """Log de inicio de paso."""
        self.step_times[step_name] = time.time()
        
        if step_number and total_steps:
            progress = f"[{step_number}/{total_steps}]"
            message = f"{self._colorize(progress, Colors.CYAN)} {step_name}"
        else:
            message = step_name
        
        self._log(LogLevel.STEP, message)
    
    def step_complete(self, step_name: str, details: Optional[str] = None):
        """Log de paso completado con tiempo."""
        elapsed = 0
        if step_name in self.step_times:
            elapsed = time.time() - self.step_times[step_name]
        
        time_str = self._colorize(f"({elapsed:.2f}s)", Colors.GREEN)
        message = f"{step_name} completado {time_str}"
        if details:
            message += f" - {details}"
        
        self._log(LogLevel.SUCCESS, message)
    
    def agent_start(self, agent_name: str, action: str):
        """Log de inicio de agente."""
        self.step_times[f"agent_{agent_name}"] = time.time()
        agent_colored = self._colorize(agent_name, Colors.MAGENTA + Colors.BOLD)
        message = f"Agente {agent_colored} iniciando: {action}"
        self._log(LogLevel.AGENT, message)
    
    def agent_complete(self, agent_name: str, result_summary: Optional[str] = None):
        """Log de agente completado."""
        elapsed = 0
        key = f"agent_{agent_name}"
        if key in self.step_times:
            elapsed = time.time() - self.step_times[key]
        
        agent_colored = self._colorize(agent_name, Colors.MAGENTA + Colors.BOLD)
        time_str = self._colorize(f"({elapsed:.2f}s)", Colors.GREEN)
        message = f"Agente {agent_colored} completado {time_str}"
        if result_summary:
            message += f"\n    └─ {result_summary}"
        
        self._log(LogLevel.SUCCESS, message)
    
    def llm_request(self, model: str, prompt_preview: str, tokens_estimate: Optional[int] = None):
        """Log de petición LLM."""
        self.step_times["llm_request"] = time.time()
        model_colored = self._colorize(model, Colors.YELLOW + Colors.BOLD)
        preview = prompt_preview[:80] + "..." if len(prompt_preview) > 80 else prompt_preview
        preview = preview.replace("\n", " ")
        
        message = f"Enviando petición a {model_colored}"
        if tokens_estimate:
            message += f" (~{tokens_estimate} tokens)"
        
        self._log(LogLevel.LLM, message)
        self.debug(f"Prompt: {self._colorize(preview, Colors.DIM)}")
    
    def llm_response(self, model: str, response_preview: str, tokens_used: Optional[int] = None):
        """Log de respuesta LLM."""
        elapsed = 0
        if "llm_request" in self.step_times:
            elapsed = time.time() - self.step_times["llm_request"]
        
        model_colored = self._colorize(model, Colors.YELLOW + Colors.BOLD)
        time_str = self._colorize(f"({elapsed:.2f}s)", Colors.GREEN)
        
        preview = response_preview[:100] + "..." if len(response_preview) > 100 else response_preview
        preview = preview.replace("\n", " ")
        
        message = f"Respuesta de {model_colored} recibida {time_str}"
        if tokens_used:
            message += f" - {tokens_used} tokens"
        
        self._log(LogLevel.LLM, message)
        self.debug(f"Respuesta: {self._colorize(preview, Colors.DIM)}")
    
    def tts_start(self, engine: str, text_length: int):
        """Log de inicio de síntesis de voz."""
        self.step_times["tts"] = time.time()
        engine_colored = self._colorize(engine, Colors.GREEN + Colors.BOLD)
        message = f"Iniciando síntesis con {engine_colored} - {text_length} caracteres"
        self._log(LogLevel.TTS, message)
    
    def tts_progress(self, current: int, total: int, current_text: Optional[str] = None):
        """Log de progreso TTS."""
        percent = (current / total) * 100 if total > 0 else 0
        bar_length = 20
        filled = int(bar_length * current / total) if total > 0 else 0
        bar = "█" * filled + "░" * (bar_length - filled)
        
        progress_colored = self._colorize(f"[{bar}] {percent:.1f}%", Colors.GREEN)
        message = f"Generando audio {progress_colored} ({current}/{total})"
        
        if current_text:
            preview = current_text[:50] + "..." if len(current_text) > 50 else current_text
            message += f"\n    └─ {self._colorize(preview, Colors.DIM)}"
        
        self._log(LogLevel.TTS, message)
    
    def tts_complete(self, duration_seconds: Optional[float] = None):
        """Log de TTS completado."""
        elapsed = 0
        if "tts" in self.step_times:
            elapsed = time.time() - self.step_times["tts"]
        
        time_str = self._colorize(f"({elapsed:.2f}s)", Colors.GREEN)
        message = f"Síntesis de voz completada {time_str}"
        if duration_seconds:
            message += f" - Audio: {duration_seconds:.1f}s"
        
        self._log(LogLevel.SUCCESS, message)
    
    def audio_processing(self, action: str, details: Optional[str] = None):
        """Log de procesamiento de audio."""
        message = action
        if details:
            message += f" - {details}"
        self._log(LogLevel.AUDIO, message)
    
    def workflow_start(self, workflow_name: str, config: Optional[Dict[str, Any]] = None):
        """Log de inicio de workflow."""
        self.start_time = time.time()
        self.step_times["workflow"] = time.time()
        
        name_colored = self._colorize(workflow_name, Colors.CYAN + Colors.BOLD)
        self._log(LogLevel.WORKFLOW, f"═══════════════════════════════════════════")
        self._log(LogLevel.WORKFLOW, f"  Iniciando workflow: {name_colored}")
        
        if config:
            for key, value in config.items():
                self.debug(f"  Config: {key} = {value}")
        
        self._log(LogLevel.WORKFLOW, f"═══════════════════════════════════════════")
    
    def workflow_complete(self, success: bool = True, summary: Optional[str] = None):
        """Log de workflow completado."""
        elapsed = 0
        if "workflow" in self.step_times:
            elapsed = time.time() - self.step_times["workflow"]
        
        self._log(LogLevel.WORKFLOW, f"═══════════════════════════════════════════")
        
        if success:
            status = self._colorize("COMPLETADO", Colors.GREEN + Colors.BOLD)
            time_str = self._colorize(f"Tiempo total: {elapsed:.2f}s", Colors.GREEN)
        else:
            status = self._colorize("FALLIDO", Colors.RED + Colors.BOLD)
            time_str = self._colorize(f"Tiempo: {elapsed:.2f}s", Colors.RED)
        
        self._log(LogLevel.WORKFLOW, f"  Workflow {status}")
        self._log(LogLevel.WORKFLOW, f"  {time_str}")
        
        if summary:
            self._log(LogLevel.WORKFLOW, f"  {summary}")
        
        self._log(LogLevel.WORKFLOW, f"═══════════════════════════════════════════")
    
    def section(self, title: str):
        """Log de sección/separador visual."""
        line = "─" * 50
        print(f"\n{self._colorize(line, Colors.CYAN)}", flush=True)
        print(f"{self._colorize(f'  {title}', Colors.CYAN + Colors.BOLD)}", flush=True)
        print(f"{self._colorize(line, Colors.CYAN)}\n", flush=True)
    
    def table(self, headers: list, rows: list):
        """Imprime datos en formato de tabla."""
        if not rows:
            return
        
        # Calcular anchos de columna
        widths = [len(str(h)) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(widths):
                    widths[i] = max(widths[i], len(str(cell)))
        
        # Imprimir encabezados
        header_str = " │ ".join(str(h).ljust(widths[i]) for i, h in enumerate(headers))
        separator = "─┼─".join("─" * w for w in widths)
        
        print(self._colorize(f"  {header_str}", Colors.BOLD), flush=True)
        print(self._colorize(f"  {separator}", Colors.DIM), flush=True)
        
        # Imprimir filas
        for row in rows:
            row_str = " │ ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row))
            print(f"  {row_str}", flush=True)
        print()
    
    def progress_bar(self, current: int, total: int, prefix: str = "", suffix: str = ""):
        """Muestra una barra de progreso."""
        if total == 0:
            return
        
        percent = current / total
        bar_length = 30
        filled = int(bar_length * percent)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        message = f"{prefix} [{self._colorize(bar, Colors.CYAN)}] {percent*100:.1f}% {suffix}"
        print(f"\r{message}", end="", flush=True)
        
        if current >= total:
            print()


class StreamingRichLogger(RichLogger):
    """
    Logger que extiende RichLogger con capacidad de streaming a callbacks.
    
    Permite capturar logs y enviarlos a Gradio u otros sistemas en tiempo real.
    """
    
    def __init__(
        self,
        name: str = "audiobook",
        level: str = "INFO",
        show_timestamp: bool = True,
        show_elapsed: bool = True,
        use_colors: bool = True,
    ):
        super().__init__(name, level, show_timestamp, show_elapsed, use_colors)
    
    def _log(self, level: LogLevel, message: str, **kwargs):
        """Override del log para notificar callbacks."""
        # Llamar al log original
        super()._log(level, message, **kwargs)
        
        # Crear entrada de log estructurada
        level_name, _, emoji = level.value
        log_entry = {
            "timestamp": self._format_time(),
            "elapsed": self._format_elapsed(),
            "level": level_name,
            "emoji": emoji,
            "message": message,
            "extra": kwargs,
            "type": "log",
        }
        
        # Notificar a callbacks
        _notify_callbacks(log_entry)
    
    def prompt(self, agent: str, prompt_text: str, system_prompt: Optional[str] = None):
        """Log de un prompt completo enviado al LLM."""
        log_entry = {
            "timestamp": self._format_time(),
            "elapsed": self._format_elapsed(),
            "level": "PROMPT",
            "emoji": "📝",
            "message": f"Prompt de {agent}",
            "type": "prompt",
            "agent": agent,
            "prompt": prompt_text,
            "system_prompt": system_prompt,
        }
        
        # Log resumido a consola
        preview = prompt_text[:100].replace("\n", " ") + "..." if len(prompt_text) > 100 else prompt_text.replace("\n", " ")
        self._log(LogLevel.LLM, f"📝 Prompt [{agent}]: {preview}")
        
        # Notificar con el prompt completo
        _notify_callbacks(log_entry)
    
    def response(self, agent: str, response_text: str, tokens: Optional[int] = None):
        """Log de una respuesta completa del LLM."""
        log_entry = {
            "timestamp": self._format_time(),
            "elapsed": self._format_elapsed(),
            "level": "RESPONSE",
            "emoji": "💬",
            "message": f"Respuesta de {agent}",
            "type": "response",
            "agent": agent,
            "response": response_text,
            "tokens": tokens,
            "word_count": len(response_text.split()) if response_text else 0,
        }
        
        # Log resumido a consola
        preview = response_text[:100].replace("\n", " ") + "..." if len(response_text) > 100 else response_text.replace("\n", " ")
        self._log(LogLevel.LLM, f"💬 Respuesta [{agent}]: {preview}")
        
        # Notificar con la respuesta completa
        _notify_callbacks(log_entry)
    
    def content_generated(self, chapter: int, title: str, content: str, agent_id: str):
        """Log de contenido de capítulo generado."""
        log_entry = {
            "timestamp": self._format_time(),
            "elapsed": self._format_elapsed(),
            "level": "CONTENT",
            "emoji": "📖",
            "message": f"Capítulo {chapter}: {title}",
            "type": "content",
            "chapter_number": chapter,
            "chapter_title": title,
            "content": content,
            "word_count": len(content.split()) if content else 0,
            "agent_id": agent_id,
        }
        
        # Notificar
        _notify_callbacks(log_entry)
    
    def evaluation_result(
        self,
        score: int,
        decision: str,
        strengths: List[str],
        weaknesses: List[str],
        feedback: Optional[str] = None,
    ):
        """Log del resultado de evaluación."""
        log_entry = {
            "timestamp": self._format_time(),
            "elapsed": self._format_elapsed(),
            "level": "EVALUATION",
            "emoji": "🔍",
            "message": f"Evaluación: {score}/100 - {decision}",
            "type": "evaluation",
            "score": score,
            "decision": decision,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "feedback": feedback,
        }
        
        # Notificar
        _notify_callbacks(log_entry)
    
    def plan_generated(self, plan: Dict[str, Any]):
        """Log del plan generado."""
        log_entry = {
            "timestamp": self._format_time(),
            "elapsed": self._format_elapsed(),
            "level": "PLAN",
            "emoji": "📋",
            "message": "Plan de contenido generado",
            "type": "plan",
            "plan": plan,
        }
        
        # Notificar
        _notify_callbacks(log_entry)


# Callback type para streaming de logs
LogCallback = Callable[[Dict[str, Any]], None]

# Logger global singleton
_logger: Optional[StreamingRichLogger] = None
_log_buffer: List[Dict[str, Any]] = []
_log_callbacks: List[LogCallback] = []


def add_log_callback(callback: LogCallback):
    """Agrega un callback para recibir logs en tiempo real."""
    global _log_callbacks
    if callback not in _log_callbacks:
        _log_callbacks.append(callback)


def remove_log_callback(callback: LogCallback):
    """Elimina un callback de logs."""
    global _log_callbacks
    if callback in _log_callbacks:
        _log_callbacks.remove(callback)


def clear_log_callbacks():
    """Limpia todos los callbacks de logs."""
    global _log_callbacks
    _log_callbacks = []


def get_log_buffer() -> list:
    """Obtiene el buffer de logs acumulados."""
    global _log_buffer
    return _log_buffer.copy()


def clear_log_buffer():
    """Limpia el buffer de logs."""
    global _log_buffer
    _log_buffer = []


def _notify_callbacks(log_entry: dict):
    """Notifica a todos los callbacks sobre un nuevo log."""
    global _log_callbacks, _log_buffer
    _log_buffer.append(log_entry)
    for callback in _log_callbacks:
        try:
            callback(log_entry)
        except Exception:
            pass  # Ignorar errores en callbacks


def get_logger(
    name: str = "audiobook",
    level: Optional[str] = None,
    force_new: bool = False,
) -> StreamingRichLogger:
    """
    Obtiene el logger singleton o crea uno nuevo.
    
    Args:
        name: Nombre del logger
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR)
        force_new: Forzar creación de nuevo logger
        
    Returns:
        Instancia del StreamingRichLogger
    """
    global _logger
    
    if _logger is None or force_new:
        log_level = level or os.environ.get("LOG_LEVEL", "INFO")
        _logger = StreamingRichLogger(
            name=name,
            level=log_level,
            use_colors=True,
        )
    
    return _logger


def setup_logging(level: str = "INFO") -> StreamingRichLogger:
    """
    Configura el sistema de logging.
    
    Args:
        level: Nivel de logging
        
    Returns:
        Logger configurado
    """
    return get_logger(level=level, force_new=True)
