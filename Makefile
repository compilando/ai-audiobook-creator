# ============================================
# Makefile para AI Audiobook Creator
# Sistema de generación de audiobooks con agentes multiagente
# ============================================

.PHONY: help install install-dev setup run test test-unit test-integration clean \
        docker-up docker-down docker-logs docker-status docker-restart \
        ollama-setup lint format check venv quick-start

# Variables
PYTHON := python
VENV := venv
VENV_BIN := $(VENV)/bin
PIP := $(VENV_BIN)/pip
PYTHON_VENV := $(VENV_BIN)/python
PORT := 7860
HOST := 0.0.0.0
OLLAMA_MODEL := qwen2.5:7b

# Colores para output
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m
BOLD := \033[1m

# ============================================
# 🚀 COMANDOS PRINCIPALES (Quick Reference)
# ============================================
# make              - Muestra ayuda
# make quick-start  - Instalación + Configuración + Ejecución
# make install      - Instala dependencias
# make run          - Ejecuta la UI
# make docker-up    - Inicia servicios Docker
# make test         - Ejecuta tests
# ============================================

help: ## Muestra esta ayuda
	@echo ""
	@echo "$(BOLD)$(CYAN)╔══════════════════════════════════════════════════════════════════╗$(RESET)"
	@echo "$(BOLD)$(CYAN)║          AI Audiobook Creator - Comandos Disponibles             ║$(RESET)"
	@echo "$(BOLD)$(CYAN)╚══════════════════════════════════════════════════════════════════╝$(RESET)"
	@echo ""
	@echo "$(BOLD)$(GREEN)🚀 COMANDOS PRINCIPALES:$(RESET)"
	@echo "  $(GREEN)quick-start$(RESET)          Instalación completa y ejecución"
	@echo "  $(GREEN)install$(RESET)              Instala dependencias"
	@echo "  $(GREEN)run$(RESET)                  Ejecuta la UI Gradio"
	@echo "  $(GREEN)docker-up$(RESET)            Inicia servicios Docker"
	@echo "  $(GREEN)test$(RESET)                 Ejecuta todos los tests"
	@echo ""
	@echo "$(BOLD)$(YELLOW)📋 TODOS LOS COMANDOS:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""

# ============================================
# 🚀 Quick Start
# ============================================

quick-start: setup run ## Instalación completa + ejecuta la aplicación

# ============================================
# Instalación y Configuración
# ============================================

venv: ## Crea el entorno virtual
	@echo "$(CYAN)Creando entorno virtual...$(RESET)"
	$(PYTHON) -m venv $(VENV)
	@echo "$(GREEN)✓ Entorno virtual creado$(RESET)"

install: venv ## Instala las dependencias del proyecto
	@echo "$(CYAN)Instalando dependencias...$(RESET)"
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)✓ Dependencias instaladas$(RESET)"

install-dev: install ## Instala dependencias de desarrollo
	@echo "$(CYAN)Instalando dependencias de desarrollo...$(RESET)"
	$(PIP) install pytest pytest-asyncio pytest-cov black isort flake8 mypy
	@echo "$(GREEN)✓ Dependencias de desarrollo instaladas$(RESET)"

setup: install ## Configuración inicial del proyecto
	@echo "$(CYAN)Configurando proyecto...$(RESET)"
	@if [ ! -f .env ]; then \
		cp env.example .env; \
		echo "$(GREEN)✓ Archivo .env creado desde env.example$(RESET)"; \
		echo "$(YELLOW)⚠ Edita .env con tu configuración$(RESET)"; \
	else \
		echo "$(YELLOW)⚠ Archivo .env ya existe$(RESET)"; \
	fi
	@mkdir -p generated_audiobooks
	@mkdir -p tests
	@echo "$(GREEN)✓ Configuración completada$(RESET)"

# ============================================
# Ejecución
# ============================================

run: ## Ejecuta la aplicación (UI Gradio)
	@echo "$(CYAN)Iniciando AI Audiobook Creator...$(RESET)"
	@echo "$(GREEN)→ Accede a http://$(HOST):$(PORT)$(RESET)"
	$(PYTHON_VENV) app.py

run-debug: ## Ejecuta la aplicación en modo debug
	@echo "$(CYAN)Iniciando en modo debug...$(RESET)"
	GRADIO_DEBUG=1 $(PYTHON_VENV) app.py

# ============================================
# Tests
# ============================================

test: ## Ejecuta todos los tests
	@echo "$(CYAN)Ejecutando todos los tests...$(RESET)"
	$(PYTHON_VENV) -m pytest tests/ -v

test-unit: ## Ejecuta tests unitarios
	@echo "$(CYAN)Ejecutando tests unitarios...$(RESET)"
	$(PYTHON_VENV) -m pytest tests/ -v -m "unit or not integration"

test-integration: ## Ejecuta tests de integración
	@echo "$(CYAN)Ejecutando tests de integración...$(RESET)"
	$(PYTHON_VENV) -m pytest tests/ -v -m integration

test-audio: ## Ejecuta el test de generación de audio sobre Materialismo Gustavo Bueno
	@echo "$(CYAN)Ejecutando test de generación de audio...$(RESET)"
	$(PYTHON_VENV) -m pytest tests/test_audiobook_generation.py -v -s

generate-audio: ## Genera un audiobook MP3 sobre Materialismo de Gustavo Bueno
	@echo "$(CYAN)Generando audiobook sobre Materialismo de Gustavo Bueno...$(RESET)"
	$(PYTHON_VENV) scripts/generate_materialismo_audio.py
	@echo "$(GREEN)✓ Audiobook generado en generated_audiobooks/materialismo_gustavo_bueno.mp3$(RESET)"

generate-audio-premium: ## Genera audiobook con Kokoro TTS (alta calidad, requiere Docker)
	@echo "$(CYAN)Generando audiobook con voz premium (Alex español)...$(RESET)"
	$(PYTHON_VENV) scripts/generate_audiobook_premium.py --voice em_alex --lang es
	@echo "$(GREEN)✓ Audiobook premium generado$(RESET)"

play-audio: ## Reproduce el audiobook generado
	@if [ -f generated_audiobooks/materialismo_gustavo_bueno.mp3 ]; then \
		echo "$(CYAN)Reproduciendo audiobook...$(RESET)"; \
		mpv generated_audiobooks/materialismo_gustavo_bueno.mp3 || \
		ffplay -nodisp -autoexit generated_audiobooks/materialismo_gustavo_bueno.mp3 || \
		echo "$(YELLOW)⚠ Instala mpv o ffplay para reproducir$(RESET)"; \
	else \
		echo "$(RED)❌ Audiobook no encontrado. Ejecuta: make generate-audio$(RESET)"; \
	fi

test-cov: ## Ejecuta tests con cobertura
	@echo "$(CYAN)Ejecutando tests con cobertura...$(RESET)"
	$(PYTHON_VENV) -m pytest tests/ -v --cov=. --cov-report=html --cov-report=term

# ============================================
# Docker
# ============================================

docker-up: ## Inicia todos los servicios con Docker Compose
	@echo "$(CYAN)Iniciando servicios Docker...$(RESET)"
	docker-compose up -d
	@echo "$(GREEN)✓ Servicios iniciados$(RESET)"
	@echo "$(GREEN)→ UI disponible en http://localhost:$(PORT)$(RESET)"

docker-down: ## Detiene todos los servicios Docker
	@echo "$(CYAN)Deteniendo servicios Docker...$(RESET)"
	docker-compose down
	@echo "$(GREEN)✓ Servicios detenidos$(RESET)"

docker-logs: ## Muestra logs de los servicios Docker
	docker-compose logs -f

docker-logs-app: ## Muestra logs de la aplicación
	docker-compose logs -f ai_audiobook_creator

docker-status: ## Muestra el estado de los servicios Docker
	@echo "$(CYAN)Estado de los servicios:$(RESET)"
	docker-compose ps

docker-restart: ## Reinicia todos los servicios Docker
	@echo "$(CYAN)Reiniciando servicios Docker...$(RESET)"
	docker-compose restart
	@echo "$(GREEN)✓ Servicios reiniciados$(RESET)"

docker-build: ## Construye la imagen Docker
	@echo "$(CYAN)Construyendo imagen Docker...$(RESET)"
	docker-compose build
	@echo "$(GREEN)✓ Imagen construida$(RESET)"

docker-clean: ## Limpia contenedores y volumenes Docker
	@echo "$(CYAN)Limpiando Docker...$(RESET)"
	docker-compose down -v --remove-orphans
	@echo "$(GREEN)✓ Docker limpiado$(RESET)"

# ============================================
# Ollama
# ============================================

ollama-setup: ## Configura Ollama y descarga el modelo por defecto
	@echo "$(CYAN)Configurando Ollama con modelo $(OLLAMA_MODEL)...$(RESET)"
	./scripts/setup-ollama.sh $(OLLAMA_MODEL)
	@echo "$(GREEN)✓ Ollama configurado$(RESET)"

ollama-pull: ## Descarga un modelo específico (uso: make ollama-pull MODEL=llama3.1)
	@echo "$(CYAN)Descargando modelo $(MODEL)...$(RESET)"
	docker exec -it ollama ollama pull $(MODEL)

ollama-list: ## Lista modelos disponibles en Ollama
	docker exec -it ollama ollama list

# ============================================
# Calidad de Código
# ============================================

lint: ## Ejecuta linter (flake8)
	@echo "$(CYAN)Ejecutando linter...$(RESET)"
	$(PYTHON_VENV) -m flake8 --max-line-length=100 --ignore=E501,W503 agents/ integration/ utils/ workflows/ app.py

format: ## Formatea el código (black + isort)
	@echo "$(CYAN)Formateando código...$(RESET)"
	$(PYTHON_VENV) -m isort agents/ integration/ utils/ workflows/ app.py tests/
	$(PYTHON_VENV) -m black --line-length=100 agents/ integration/ utils/ workflows/ app.py tests/
	@echo "$(GREEN)✓ Código formateado$(RESET)"

check: lint ## Verifica el código (lint + type check)
	@echo "$(CYAN)Verificando tipos...$(RESET)"
	$(PYTHON_VENV) -m mypy --ignore-missing-imports agents/ integration/ utils/ workflows/

# ============================================
# Limpieza
# ============================================

clean: ## Limpia archivos temporales y cache
	@echo "$(CYAN)Limpiando archivos temporales...$(RESET)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage 2>/dev/null || true
	@echo "$(GREEN)✓ Limpieza completada$(RESET)"

clean-all: clean ## Limpieza completa (incluye venv y audiobooks generados)
	@echo "$(CYAN)Limpieza completa...$(RESET)"
	rm -rf $(VENV) 2>/dev/null || true
	rm -rf generated_audiobooks/* 2>/dev/null || true
	@echo "$(GREEN)✓ Limpieza completa$(RESET)"

# ============================================
# Utilidades
# ============================================

info: ## Muestra información del sistema
	@echo "$(CYAN)Información del Sistema:$(RESET)"
	@echo "  Python: $$($(PYTHON) --version)"
	@if [ -d $(VENV) ]; then \
		echo "  Venv Python: $$($$(PYTHON_VENV) --version)"; \
	fi
	@echo "  Docker: $$(docker --version 2>/dev/null || echo 'No instalado')"
	@echo "  Docker Compose: $$(docker-compose --version 2>/dev/null || echo 'No instalado')"
	@echo ""
	@echo "$(CYAN)Configuración:$(RESET)"
	@if [ -f .env ]; then \
		echo "  LLM_BASE_URL: $$(grep LLM_BASE_URL .env | head -1 | cut -d= -f2)"; \
		echo "  TTS_BASE_URL: $$(grep TTS_BASE_URL .env | head -1 | cut -d= -f2)"; \
		echo "  DEFAULT_LANGUAGE: $$(grep DEFAULT_LANGUAGE .env | cut -d= -f2)"; \
	else \
		echo "  $(YELLOW)⚠ Archivo .env no encontrado$(RESET)"; \
	fi

check-services: ## Verifica que los servicios externos estén disponibles
	@echo "$(CYAN)Verificando servicios...$(RESET)"
	@echo -n "  LLM (localhost:1234): "
	@curl -s --connect-timeout 2 http://localhost:1234/v1/models > /dev/null 2>&1 && echo "$(GREEN)✓ OK$(RESET)" || echo "$(RED)✗ No disponible$(RESET)"
	@echo -n "  TTS (localhost:8880): "
	@curl -s --connect-timeout 2 http://localhost:8880/health > /dev/null 2>&1 && echo "$(GREEN)✓ OK$(RESET)" || echo "$(RED)✗ No disponible$(RESET)"
	@echo -n "  Ollama (localhost:11434): "
	@curl -s --connect-timeout 2 http://localhost:11434/api/tags > /dev/null 2>&1 && echo "$(GREEN)✓ OK$(RESET)" || echo "$(RED)✗ No disponible$(RESET)"
