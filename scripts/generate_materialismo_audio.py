#!/usr/bin/env python3
"""
Script para generar un audiobook sobre el Materialismo Filosófico de Gustavo Bueno.

Este script genera un archivo MP3 completo usando gTTS (Google Text-to-Speech).
No requiere servicios externos locales, solo conexión a internet.

Uso:
    python scripts/generate_materialismo_audio.py
    
    O con el Makefile:
    make test-audio
"""

import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))


def generate_materialismo_audiobook():
    """
    Genera un audiobook completo sobre el Materialismo Filosófico de Gustavo Bueno.
    """
    try:
        from gtts import gTTS
    except ImportError:
        print("❌ Error: gTTS no está instalado.")
        print("   Instala con: pip install gTTS")
        return None
    
    print("=" * 70)
    print("🎧 Generando Audiobook: Materialismo Filosófico de Gustavo Bueno")
    print("=" * 70)
    
    # Contenido sobre Materialismo Filosófico de Gustavo Bueno
    contenido = """
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
    
    # Crear directorio de salida
    output_dir = ROOT_DIR / "generated_audiobooks"
    output_dir.mkdir(exist_ok=True)
    
    # Nombre del archivo de salida
    output_file = output_dir / "materialismo_gustavo_bueno.mp3"
    text_file = output_dir / "materialismo_gustavo_bueno.txt"
    
    # Guardar el texto
    with open(text_file, "w", encoding="utf-8") as f:
        f.write(contenido)
    print(f"📝 Texto guardado en: {text_file}")
    
    # Generar audio
    print("\n🔊 Generando audio con gTTS (Google Text-to-Speech)...")
    print("   Esto puede tomar unos minutos...")
    
    try:
        tts = gTTS(text=contenido, lang='es', slow=False)
        tts.save(str(output_file))
        
        # Obtener información del archivo
        file_size = output_file.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"\n✅ ¡Audiobook generado exitosamente!")
        print(f"📁 Archivo: {output_file}")
        print(f"📊 Tamaño: {file_size_mb:.2f} MB")
        print(f"🎵 Formato: MP3")
        
        # Calcular duración aproximada
        word_count = len(contenido.split())
        # Aproximadamente 150 palabras por minuto
        duration_minutes = word_count / 150
        print(f"⏱️  Duración aproximada: {duration_minutes:.1f} minutos")
        
        print("\n" + "=" * 70)
        print("🎧 Para reproducir el audiobook:")
        print(f"   mpv {output_file}")
        print(f"   # o con cualquier reproductor de audio")
        print("=" * 70)
        
        return str(output_file)
        
    except Exception as e:
        print(f"\n❌ Error al generar audio: {e}")
        print("   Asegúrate de tener conexión a internet.")
        return None


def main():
    """Punto de entrada principal."""
    output_path = generate_materialismo_audiobook()
    
    if output_path:
        print(f"\n✅ Proceso completado. Archivo generado: {output_path}")
        return 0
    else:
        print("\n❌ No se pudo generar el audiobook.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
