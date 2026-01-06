#!/bin/bash

# Script de ayuda para gestión de Docker Compose

echo "🎧 AI Audiobook Creator - Comandos Docker"
echo "=========================================="
echo ""

case "$1" in
    start)
        echo "🚀 Iniciando servicios..."
        docker-compose up -d
        echo ""
        echo "⏳ Esperando a que los servicios estén listos..."
        sleep 10
        echo ""
        echo "📋 Estado de servicios:"
        docker-compose ps
        echo ""
        echo "💡 Para configurar Ollama, ejecuta: ./scripts/setup-ollama.sh"
        echo "🌐 Accede a la UI en: http://localhost:7860"
        ;;
    
    stop)
        echo "🛑 Deteniendo servicios..."
        docker-compose down
        ;;
    
    restart)
        echo "🔄 Reiniciando servicios..."
        docker-compose restart
        ;;
    
    logs)
        SERVICE=${2:-""}
        if [ -z "$SERVICE" ]; then
            echo "📜 Mostrando logs de todos los servicios..."
            docker-compose logs -f
        else
            echo "📜 Mostrando logs de $SERVICE..."
            docker-compose logs -f "$SERVICE"
        fi
        ;;
    
    status)
        echo "📋 Estado de servicios:"
        docker-compose ps
        echo ""
        echo "💾 Uso de volúmenes:"
        docker volume ls | grep ai_audiobook
        ;;
    
    clean)
        echo "🧹 Limpiando contenedores, volúmenes y redes..."
        docker-compose down -v
        echo "✅ Limpieza completada"
        ;;
    
    rebuild)
        echo "🔨 Reconstruyendo imagen de la aplicación..."
        docker-compose build --no-cache ai_audiobook_creator
        echo "✅ Reconstrucción completada"
        ;;
    
    shell)
        echo "🐚 Abriendo shell en el contenedor..."
        docker-compose exec ai_audiobook_creator /bin/bash
        ;;
    
    *)
        echo "Uso: $0 {start|stop|restart|logs|status|clean|rebuild|shell}"
        echo ""
        echo "Comandos disponibles:"
        echo "  start     - Inicia todos los servicios"
        echo "  stop      - Detiene todos los servicios"
        echo "  restart   - Reinicia todos los servicios"
        echo "  logs      - Muestra logs (opcional: nombre del servicio)"
        echo "  status    - Muestra estado de servicios y volúmenes"
        echo "  clean     - Limpia contenedores, volúmenes y redes"
        echo "  rebuild   - Reconstruye la imagen de la aplicación"
        echo "  shell     - Abre shell en el contenedor principal"
        echo ""
        echo "Ejemplos:"
        echo "  $0 start"
        echo "  $0 logs ollama"
        echo "  $0 shell"
        exit 1
        ;;
esac
