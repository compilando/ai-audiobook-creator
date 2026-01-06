#!/bin/bash

# Script para configurar Ollama después de iniciar el contenedor
# Uso: ./scripts/setup-ollama.sh [modelo]

MODEL=${1:-"qwen2.5:7b"}

echo "🚀 Configurando Ollama con modelo: $MODEL"
echo ""

# Verificar que el contenedor está corriendo
if ! docker ps | grep -q ai_audiobook_ollama; then
    echo "❌ Error: El contenedor ai_audiobook_ollama no está corriendo"
    echo "   Inicia los servicios primero con: docker-compose up -d"
    exit 1
fi

echo "📥 Descargando modelo $MODEL..."
docker exec -it ai_audiobook_ollama ollama pull "$MODEL"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Modelo $MODEL descargado exitosamente"
    echo ""
    echo "📋 Modelos disponibles:"
    docker exec -it ai_audiobook_ollama ollama list
    echo ""
    echo "💡 Para usar este modelo, actualiza LLM_MODEL_NAME en .env o docker-compose.yml"
else
    echo ""
    echo "❌ Error al descargar el modelo"
    exit 1
fi
