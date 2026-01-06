"""
Módulos de integración con el sistema de audiobook existente.
"""

from .audiobook_adapter import AudiobookAdapter
from .content_formatter import ContentFormatter

__all__ = ["AudiobookAdapter", "ContentFormatter"]
