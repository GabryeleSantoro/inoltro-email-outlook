"""Servizio HTTP interrogato da Power Automate."""

from .app import create_app

__all__ = ["create_app"]
