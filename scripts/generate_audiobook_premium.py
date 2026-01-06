#!/usr/bin/env python3
"""
Script para generar un audiobook con voz de alta calidad.

Este script intenta usar los servicios de Docker (Kokoro TTS) para mejor calidad,
y hace fallback a gTTS si no están disponibles.

Voces disponibles en Kokoro TTS:
- af_sky: Voz femenina americana (Sky) - Muy natural
- af_nicole: Voz femenina americana (Nicole) - Clara y profesional
- bf_emma: Voz femenina británica (Emma) - Elegante
- am_adam: Voz masculina americana (Adam) - Profunda
- bm_george: Voz masculina británica (George) - Autoritativa
- ef_dora: Voz femenina española (Dora) - Para español
- em_alex: Voz masculina española (Alex) - Para español

Uso:
    python scripts/generate_audiobook_premium.py
    python scripts/generate_audiobook_premium.py --voice ef_dora --lang es
    python scripts/generate_audiobook_premium.py --voice af_sky --lang en
"""

import os
import sys
import argparse
import urllib.request
import urllib.error
import json
from pathlib import Path

# Agregar el directorio raíz al path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

# URLs de servicios
KOKORO_TTS_URL = "http://localhost:8880"
OLLAMA_URL = "http://localhost:11434"


def check_service(url: str, endpoint: str = "/health") -> bool:
    """Verifica si un servicio está disponible."""
    try:
        urllib.request.urlopen(f"{url}{endpoint}", timeout=2)
        return True
    except Exception:
        return False


def get_available_voices() -> list:
    """Obtiene las voces disponibles en Kokoro TTS."""
    try:
        req = urllib.request.Request(f"{KOKORO_TTS_URL}/v1/audio/voices")
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            return data.get("voices", [])
    except Exception:
        return []


def generate_with_kokoro(text: str, output_path: str, voice: str = "ef_dora", language: str = "es") -> bool:
    """
    Genera audio usando Kokoro TTS (alta calidad).
    
    Args:
        text: Texto a convertir
        output_path: Ruta del archivo de salida
        voice: ID de la voz a usar
        language: Idioma del texto
        
    Returns:
        True si se generó exitosamente
    """
    print(f"🎤 Usando voz: {voice}")
    print(f"🌍 Idioma: {language}")
    
    # Kokoro usa API compatible con OpenAI
    payload = json.dumps({
        "model": "kokoro",
        "input": text,
        "voice": voice,
        "response_format": "mp3",
        "speed": 1.0
    }).encode('utf-8')
    
    headers = {
        "Content-Type": "application/json"
    }
    
    req = urllib.request.Request(
        f"{KOKORO_TTS_URL}/v1/audio/speech",
        data=payload,
        headers=headers,
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=300) as response:
            with open(output_path, "wb") as f:
                f.write(response.read())
        return True
    except Exception as e:
        print(f"❌ Error con Kokoro TTS: {e}")
        return False


def generate_with_gtts(text: str, output_path: str, language: str = "es") -> bool:
    """
    Genera audio usando gTTS (fallback).
    
    Args:
        text: Texto a convertir
        output_path: Ruta del archivo de salida
        language: Idioma del texto
        
    Returns:
        True si se generó exitosamente
    """
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang=language, slow=False)
        tts.save(output_path)
        return True
    except Exception as e:
        print(f"❌ Error con gTTS: {e}")
        return False


def get_materialismo_content() -> str:
    """Retorna el contenido sobre Materialismo de Gustavo Bueno."""
    return """
    Capítulo 1: Introducción al Materialismo Filosófico.
    
    El Materialismo Filosófico es un sistema filosófico desarrollado por 
    Gustavo Bueno Martínez. Nacido en Santo Domingo de la Calzada en mil 
    novecientos veinticuatro y fallecido en Niembro, Asturias, en dos mil 
    dieciséis, Gustavo Bueno es considerado uno de los filósofos más 
    importantes de la España contemporánea.
    
    Este sistema representa una de las contribuciones más originales y 
    sistemáticas a la filosofía contemporánea en lengua española. Gustavo 
    Bueno fundó la Escuela de Oviedo y desarrolló su obra a lo largo de 
    más de cinco décadas.
    
    El Materialismo Filosófico no debe confundirse con el materialismo 
    vulgar ni con el materialismo dialéctico marxista. Se trata de un 
    sistema que parte de la crítica a todo idealismo, pero también supera 
    las limitaciones del materialismo monista tradicional.
    
    Capítulo 2: Los Tres Géneros de Materialidad.
    
    Una de las ideas centrales del Materialismo Filosófico es la 
    distinción entre tres géneros de materialidad ontológica.
    
    El primer género de materialidad, también llamado M uno, comprende 
    todas las entidades físicas y corpóreas. Es el ámbito de lo que 
    tradicionalmente se ha llamado materia, pero entendido de manera 
    más amplia. Incluye desde las partículas elementales hasta los 
    organismos vivos y las galaxias.
    
    El segundo género de materialidad, M dos, abarca los procesos 
    psicológicos, las operaciones mentales, las vivencias internas. 
    No se trata de un espiritualismo, sino del reconocimiento de que 
    los procesos psíquicos tienen una materialidad propia, irreductible 
    a los procesos físicos.
    
    El tercer género de materialidad, M tres, comprende los objetos 
    abstractos pero objetivos, como las estructuras matemáticas, los 
    teoremas, las relaciones lógicas. Estos objetos no son meras 
    construcciones subjetivas, sino que tienen una consistencia propia, 
    aunque no física.
    
    Capítulo 3: La Teoría del Cierre Categorial.
    
    La Teoría del Cierre Categorial constituye la gnoseología del 
    Materialismo Filosófico, es decir, su teoría del conocimiento 
    científico. Esta teoría ofrece una explicación materialista de 
    cómo se construyen las ciencias y cuál es el fundamento de la 
    verdad científica.
    
    Según Gustavo Bueno, una ciencia se constituye cuando logra 
    establecer un cierre categorial. Esto significa que las operaciones 
    realizadas con los términos del campo producen nuevos términos que 
    pertenecen al mismo campo, formando un sistema cerrado de 
    identidades sintéticas.
    
    Por ejemplo, en química, las operaciones con elementos producen 
    compuestos que siguen siendo entidades químicas. En matemáticas, 
    las operaciones con números producen otros números. Este cierre 
    garantiza la objetividad y la verdad del conocimiento científico, 
    sin recurrir a instancias trascendentes ni a sujetos cognoscentes 
    abstractos.
    
    La Teoría del Cierre Categorial permite distinguir las ciencias 
    genuinas de las pseudociencias y de las disciplinas que no han 
    alcanzado el estatuto de cientificidad plena.
    
    Capítulo 4: Aplicaciones del Materialismo Filosófico.
    
    El Materialismo Filosófico no es solo un sistema teórico abstracto, 
    sino que tiene aplicaciones en múltiples campos del conocimiento 
    y la cultura.
    
    En el ámbito político, Gustavo Bueno desarrolló una teoría del 
    Estado y de las naciones que critica tanto el nacionalismo como 
    el cosmopolitismo ingenuo. Su análisis de España y de las 
    comunidades políticas ha generado importantes debates intelectuales.
    
    En filosofía de la religión, el Materialismo Filosófico propone 
    una interpretación de los fenómenos religiosos que no recurre a 
    explicaciones sobrenaturales, pero tampoco reduce la religión a 
    mera superstición. Bueno desarrolló una filosofía de la religión 
    que analiza el núcleo y el cuerpo de las distintas religiones.
    
    En estética y filosofía del arte, el sistema ofrece herramientas 
    para analizar las diferentes artes y sus relaciones, superando 
    tanto las visiones idealistas como las meramente sociológicas.
    
    El Materialismo Filosófico sigue siendo desarrollado por 
    discípulos y continuadores de la Escuela de Oviedo, demostrando 
    su vitalidad y su capacidad para abordar nuevos problemas del 
    siglo veintiuno.
    
    Fin del audiobook sobre el Materialismo Filosófico de Gustavo Bueno.
    """


def main():
    """Punto de entrada principal."""
    parser = argparse.ArgumentParser(description="Genera audiobook con voz de alta calidad")
    parser.add_argument("--voice", type=str, default="em_alex",
                       help="Voz a usar (em_alex, ef_dora, af_sky, bf_emma, am_adam, etc.)")
    parser.add_argument("--lang", type=str, default="es",
                       help="Idioma (es, en)")
    parser.add_argument("--output", type=str, default=None,
                       help="Archivo de salida")
    args = parser.parse_args()
    
    print("=" * 70)
    print("🎧 Generador de Audiobook Premium")
    print("   Materialismo Filosófico de Gustavo Bueno")
    print("=" * 70)
    
    # Verificar servicios
    kokoro_available = check_service(KOKORO_TTS_URL, "/health")
    
    print("\n📡 Estado de servicios:")
    print(f"   Kokoro TTS: {'✅ Disponible' if kokoro_available else '❌ No disponible'}")
    
    # Configurar salida
    output_dir = ROOT_DIR / "generated_audiobooks"
    output_dir.mkdir(exist_ok=True)
    
    if args.output:
        output_file = Path(args.output)
    else:
        suffix = "_premium" if kokoro_available else ""
        output_file = output_dir / f"materialismo_gustavo_bueno{suffix}.mp3"
    
    # Obtener contenido
    content = get_materialismo_content()
    
    # Guardar texto
    text_file = output_dir / "materialismo_gustavo_bueno.txt"
    with open(text_file, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\n📝 Texto guardado en: {text_file}")
    
    # Generar audio
    print("\n🔊 Generando audio...")
    
    success = False
    if kokoro_available:
        print(f"   Usando Kokoro TTS (alta calidad)")
        
        # Mostrar voces disponibles
        voices = get_available_voices()
        if voices:
            print(f"   Voces disponibles: {', '.join(voices[:5])}...")
        
        success = generate_with_kokoro(
            content, 
            str(output_file), 
            voice=args.voice,
            language=args.lang
        )
    
    if not success:
        print("   Usando gTTS (fallback)")
        success = generate_with_gtts(content, str(output_file), language=args.lang)
    
    if success and output_file.exists():
        file_size = output_file.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"\n✅ ¡Audiobook generado exitosamente!")
        print(f"📁 Archivo: {output_file}")
        print(f"📊 Tamaño: {file_size_mb:.2f} MB")
        print(f"🎵 Motor: {'Kokoro TTS' if kokoro_available else 'gTTS'}")
        
        if kokoro_available:
            print(f"🎤 Voz: {args.voice}")
            print("\n💡 Voces recomendadas para español:")
            print("   ef_dora - Voz femenina española (Dora)")
            print("   em_alex - Voz masculina española (Alex)")
        
        print("\n" + "=" * 70)
        print("🎧 Para reproducir:")
        print(f"   mpv {output_file}")
        print("=" * 70)
        
        return 0
    else:
        print("\n❌ No se pudo generar el audiobook")
        return 1


if __name__ == "__main__":
    sys.exit(main())
