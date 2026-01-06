"""
Cliente LLM unificado que soporta diferentes backends OpenAI-compatible.
"""

import os
from typing import Optional, List, Dict, Any
from openai import OpenAI, AsyncOpenAI
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from utils.rich_logger import get_logger

load_dotenv()


class LLMClient:
    """Cliente unificado para comunicación con LLMs."""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ):
        """
        Inicializa el cliente LLM.
        
        Args:
            base_url: URL base del API (por defecto desde env)
            api_key: Clave API (por defecto desde env)
            model_name: Nombre del modelo (por defecto desde env)
            temperature: Temperatura para generación
            max_tokens: Máximo de tokens a generar (default 4096)
        """
        self.base_url = base_url or os.environ.get(
            "LLM_BASE_URL", "http://localhost:11434/v1"
        )
        self.api_key = api_key or os.environ.get(
            "LLM_API_KEY", "not-needed"
        )
        self.model_name = model_name or os.environ.get(
            "LLM_MODEL_NAME", "qwen2.5:7b"
        )
        self.temperature = temperature
        # Establecer max_tokens por defecto desde env o 4096
        self.max_tokens = max_tokens or int(os.environ.get("LLM_MAX_TOKENS", "4096"))
        
        # Cliente síncrono
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )
        
        # Cliente asíncrono
        self.async_client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )
        
        # Cliente LangChain para integración con LangGraph
        self.langchain_client = ChatOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Genera texto usando el LLM de forma síncrona.
        
        Args:
            prompt: Prompt del usuario
            system_prompt: Prompt del sistema (opcional)
            temperature: Temperatura (opcional, usa la del cliente si no se especifica)
            
        Returns:
            Texto generado
        """
        logger = get_logger()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Estimar tokens (aproximado: ~4 chars por token)
        total_chars = len(prompt) + (len(system_prompt) if system_prompt else 0)
        tokens_estimate = total_chars // 4
        
        logger.llm_request(self.model_name, prompt, tokens_estimate)
        
        # Capturar prompt completo para streaming a Gradio
        if hasattr(logger, 'prompt'):
            logger.prompt(self.model_name, prompt, system_prompt)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=self.max_tokens,
            )
            
            content = response.choices[0].message.content
            result = content.strip() if content else ""
            
            # Obtener tokens usados si está disponible
            tokens_used = None
            if hasattr(response, 'usage') and response.usage:
                tokens_used = response.usage.total_tokens
            
            logger.llm_response(self.model_name, result, tokens_used)
            
            # Capturar respuesta completa para streaming a Gradio
            if hasattr(logger, 'response'):
                logger.response(self.model_name, result, tokens_used)
            
            return result
        except Exception as e:
            logger.error(f"Error en LLM generate: {type(e).__name__}: {str(e)}")
            logger.error(f"  URL: {self.base_url}, Modelo: {self.model_name}")
            raise
    
    async def generate_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Genera texto usando el LLM de forma asíncrona.
        
        Args:
            prompt: Prompt del usuario
            system_prompt: Prompt del sistema (opcional)
            temperature: Temperatura (opcional, usa la del cliente si no se especifica)
            
        Returns:
            Texto generado
        """
        logger = get_logger()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Estimar tokens (aproximado: ~4 chars por token)
        total_chars = len(prompt) + (len(system_prompt) if system_prompt else 0)
        tokens_estimate = total_chars // 4
        
        logger.llm_request(self.model_name, prompt, tokens_estimate)
        
        # Capturar prompt completo para streaming a Gradio
        if hasattr(logger, 'prompt'):
            logger.prompt(self.model_name, prompt, system_prompt)
        
        try:
            response = await self.async_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=self.max_tokens,
            )
            
            content = response.choices[0].message.content
            result = content.strip() if content else ""
            
            # Obtener tokens usados si está disponible
            tokens_used = None
            if hasattr(response, 'usage') and response.usage:
                tokens_used = response.usage.total_tokens
            
            logger.llm_response(self.model_name, result, tokens_used)
            
            # Capturar respuesta completa para streaming a Gradio
            if hasattr(logger, 'response'):
                logger.response(self.model_name, result, tokens_used)
            
            return result
        except Exception as e:
            logger.error(f"Error en LLM generate_async: {type(e).__name__}: {str(e)}")
            logger.error(f"  URL: {self.base_url}, Modelo: {self.model_name}")
            raise
    
    def get_langchain_client(self) -> ChatOpenAI:
        """Retorna el cliente LangChain para uso con LangGraph."""
        return self.langchain_client


def create_llm_client_for_agent(
    agent_name: str,
    base_url_env: Optional[str] = None,
    api_key_env: Optional[str] = None,
    model_env: Optional[str] = None,
    default_base_url: str = "http://localhost:11434/v1",
    default_api_key: str = "not-needed",
    default_model: str = "qwen2.5:7b",
) -> LLMClient:
    """
    Crea un cliente LLM específico para un agente.
    
    Permite usar diferentes modelos/configuraciones para cada agente.
    
    Args:
        agent_name: Nombre del agente (para prefijos de env vars)
        base_url_env: Nombre de la variable de entorno para base_url
        api_key_env: Nombre de la variable de entorno para api_key
        model_env: Nombre de la variable de entorno para model
        default_base_url: URL por defecto
        default_api_key: API key por defecto
        default_model: Modelo por defecto
        
    Returns:
        Cliente LLM configurado
    """
    # Primero buscar variable específica del agente, luego la general, luego el default
    agent_base_url_var = f"{agent_name.upper()}_LLM_BASE_URL"
    base_url = os.environ.get(
        base_url_env or agent_base_url_var,
        os.environ.get("LLM_BASE_URL", default_base_url)
    )
    
    agent_api_key_var = f"{agent_name.upper()}_LLM_API_KEY"
    api_key = os.environ.get(
        api_key_env or agent_api_key_var,
        os.environ.get("LLM_API_KEY", default_api_key)
    )
    
    agent_model_var = f"{agent_name.upper()}_LLM_MODEL_NAME"
    model = os.environ.get(
        model_env or agent_model_var,
        os.environ.get("LLM_MODEL_NAME", default_model)
    )
    
    return LLMClient(
        base_url=base_url,
        api_key=api_key,
        model_name=model,
    )
