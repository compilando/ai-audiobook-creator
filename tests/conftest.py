"""
Configuración de pytest para los tests de AI Audiobook Creator.
"""

import os
import sys
import pytest

# Agregar el directorio raíz al path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


def pytest_configure(config):
    """Configuración de pytest."""
    # Registrar markers personalizados
    config.addinivalue_line(
        "markers", "integration: tests de integración que requieren servicios externos"
    )
    config.addinivalue_line(
        "markers", "unit: tests unitarios que no requieren servicios externos"
    )
    config.addinivalue_line(
        "markers", "slow: tests que tardan más de lo normal"
    )


@pytest.fixture(scope="session")
def project_root():
    """Retorna el directorio raíz del proyecto."""
    return ROOT_DIR


@pytest.fixture(scope="session")
def output_dir(project_root):
    """Crea y retorna el directorio de salida para tests."""
    output = os.path.join(project_root, "generated_audiobooks")
    os.makedirs(output, exist_ok=True)
    return output


@pytest.fixture(scope="session")
def services_status():
    """
    Verifica el estado de los servicios externos.
    
    Returns:
        Dict con el estado de cada servicio
    """
    import urllib.request
    import urllib.error
    
    services = {
        "llm": {
            "url": "http://localhost:1234/v1/models",
            "name": "LLM (LM Studio)",
        },
        "ollama": {
            "url": "http://localhost:11434/api/tags",
            "name": "Ollama",
        },
        "tts": {
            "url": "http://localhost:8880/health",
            "name": "TTS (Kokoro/Orpheus)",
        },
    }
    
    status = {}
    for key, info in services.items():
        try:
            urllib.request.urlopen(info["url"], timeout=2)
            status[key] = {
                "available": True,
                "name": info["name"],
                "url": info["url"],
            }
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, Exception):
            status[key] = {
                "available": False,
                "name": info["name"],
                "url": info["url"],
            }
    
    return status


@pytest.fixture
def require_llm(services_status):
    """Fixture que salta el test si LLM no está disponible."""
    if not services_status.get("llm", {}).get("available") and \
       not services_status.get("ollama", {}).get("available"):
        pytest.skip("Ningún servicio LLM disponible")


@pytest.fixture
def require_tts(services_status):
    """Fixture que salta el test si TTS no está disponible."""
    if not services_status.get("tts", {}).get("available"):
        pytest.skip("Servicio TTS no disponible")


@pytest.fixture(autouse=True)
def setup_env(project_root):
    """Configura variables de entorno para tests."""
    # Cargar .env si existe (desde el directorio del proyecto)
    env_file = os.path.join(project_root, ".env")
    if os.path.exists(env_file):
        from dotenv import load_dotenv
        load_dotenv(env_file)
    
    # Establecer valores por defecto para tests
    os.environ.setdefault("MAX_ITERATIONS", "1")
    os.environ.setdefault("QUALITY_THRESHOLD", "50.0")
    os.environ.setdefault("DEFAULT_LANGUAGE", "es")
