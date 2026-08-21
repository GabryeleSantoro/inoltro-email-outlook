"""Servizio HTTP di analisi delle email di telemedicina.

Riceve da Power Automate una email per volta, verifica che oggetto e corpo
parlino di telemedicina o televisita, legge allegati e foto con l'OCR cercando
i criteri configurati ("telemedicina" e il codice "1501A") e restituisce anche
un punteggio di sentiment e di intento di prenotazione.
"""

__version__ = "2.0.0"
