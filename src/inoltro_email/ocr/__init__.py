"""Lettura locale del testo degli allegati (PaddleOCR + PDF)."""

from .extractor import TextExtractor
from .paddle import OcrError, PaddleOcrClient

__all__ = ["TextExtractor", "PaddleOcrClient", "OcrError"]
