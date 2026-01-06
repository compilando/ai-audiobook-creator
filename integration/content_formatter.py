"""
Formateador de contenido que prepara el contenido generado para el sistema de audiobook.
"""

from typing import List, Dict, Any, Optional
import os


class ContentFormatter:
    """Formatea el contenido generado al formato esperado por audiobook-creator."""
    
    @staticmethod
    def format_to_audiobook_text(
        content: List[Dict[str, Any]],
        output_path: str = "converted_book.txt",
        language: str = "es",
    ) -> str:
        """
        Formatea el contenido generado al formato de texto plano para audiobook.
        
        Args:
            content: Lista de capítulos con contenido
            output_path: Ruta donde guardar el archivo formateado
            language: Código de idioma ("es" para español, "en" para inglés)
            
        Returns:
            Ruta del archivo generado
        """
        # Determinar el prefijo de capítulo según el idioma
        chapter_prefix = "Capítulo" if language == "es" else "Chapter"
        
        formatted_lines = []
        
        for chapter in sorted(content, key=lambda x: x.get("chapter_number", 0)):
            chapter_num = chapter.get("chapter_number", 0)
            chapter_title = chapter.get("chapter_title", "")
            chapter_content = chapter.get("content", "")
            
            # Agregar título del capítulo en el idioma correcto
            formatted_lines.append(f"{chapter_prefix} {chapter_num}")
            if chapter_title:
                formatted_lines.append(chapter_title)
            formatted_lines.append("")  # Línea en blanco
            
            # Agregar contenido del capítulo
            # Dividir en párrafos y líneas
            if chapter_content:
                paragraphs = chapter_content.split("\n\n")
                for paragraph in paragraphs:
                    if paragraph.strip():
                        # Dividir párrafos largos en líneas más cortas para mejor TTS
                        lines = ContentFormatter._split_paragraph_for_tts(paragraph)
                        formatted_lines.extend(lines)
                        formatted_lines.append("")  # Línea en blanco entre párrafos
        
        # Escribir al archivo
        formatted_text = "\n".join(formatted_lines)
        
        # Asegurar que el directorio existe
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(formatted_text)
        
        return output_path
    
    @staticmethod
    def _split_paragraph_for_tts(text: str, max_line_length: int = 100) -> List[str]:
        """
        Divide un párrafo en líneas apropiadas para TTS.
        
        Args:
            text: Texto del párrafo
            max_line_length: Longitud máxima por línea
            
        Returns:
            Lista de líneas
        """
        lines = []
        sentences = text.split(". ")
        
        current_line = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Agregar punto si no termina con puntuación
            if not sentence[-1] in ".!?":
                sentence += "."
            
            # Si la línea actual más la oración es muy larga, empezar nueva línea
            if current_line and len(current_line) + len(sentence) + 1 > max_line_length:
                lines.append(current_line.strip())
                current_line = sentence
            else:
                if current_line:
                    current_line += " " + sentence
                else:
                    current_line = sentence
        
        if current_line:
            lines.append(current_line.strip())
        
        return lines
    
    @staticmethod
    def merge_best_content(
        content_v1: Optional[List[Dict[str, Any]]],
        content_v2: Optional[List[Dict[str, Any]]],
        evaluation: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Fusiona el mejor contenido de ambos generadores basándose en la evaluación.
        
        Args:
            content_v1: Contenido del generador 1
            content_v2: Contenido del generador 2
            evaluation: Evaluación del contenido
            
        Returns:
            Lista de capítulos con el mejor contenido fusionado
        """
        if not content_v1 and not content_v2:
            return []
        
        if not content_v1:
            return content_v2 or []
        
        if not content_v2:
            return content_v1
        
        # Obtener scores por capítulo de la evaluación
        scores_by_chapter = evaluation.get("scores_by_chapter", []) if evaluation else []
        scores_dict = {item.get("chapter"): item.get("score", 0) for item in scores_by_chapter}
        
        # Crear diccionario de contenido por número de capítulo
        content_v1_dict = {ch.get("chapter_number"): ch for ch in content_v1}
        content_v2_dict = {ch.get("chapter_number"): ch for ch in content_v2}
        
        # Fusionar seleccionando el mejor contenido por capítulo
        merged_content = []
        all_chapter_nums = sorted(set(list(content_v1_dict.keys()) + list(content_v2_dict.keys())))
        
        for chapter_num in all_chapter_nums:
            ch1 = content_v1_dict.get(chapter_num)
            ch2 = content_v2_dict.get(chapter_num)
            
            if not ch1:
                merged_content.append(ch2)
            elif not ch2:
                merged_content.append(ch1)
            else:
                # Comparar scores si están disponibles
                score_v1 = scores_dict.get(chapter_num, 0)
                score_v2 = scores_dict.get(chapter_num, 0)
                
                # Si no hay scores, usar el contenido más largo
                if score_v1 == score_v2 == 0:
                    if len(ch1.get("content", "")) > len(ch2.get("content", "")):
                        merged_content.append(ch1)
                    else:
                        merged_content.append(ch2)
                else:
                    # Usar el contenido con mejor score
                    if score_v1 >= score_v2:
                        merged_content.append(ch1)
                    else:
                        merged_content.append(ch2)
        
        return merged_content
