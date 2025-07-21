"""Módulo de indexação de diferentes tipos de dados."""

from .text_indexer import TextIndexer
from .pdf_indexer import PDFIndexer  
from .video_indexer import VideoIndexer
from .image_indexer import ImageIndexer

__all__ = ['TextIndexer', 'PDFIndexer', 'VideoIndexer', 'ImageIndexer'] 