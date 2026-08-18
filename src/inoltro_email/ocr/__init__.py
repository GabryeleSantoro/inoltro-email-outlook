"""Lettura del testo degli allegati (ocr.space + livello testo dei PDF)."""

from .extractor import TextExtractor
from .ocrspace import OcrSpaceClient, OcrSpaceError

__all__ = ["TextExtractor", "OcrSpaceClient", "OcrSpaceError"]
