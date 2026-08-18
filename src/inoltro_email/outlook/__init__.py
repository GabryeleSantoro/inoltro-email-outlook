"""Integrazione con la casella Outlook tramite Microsoft Graph (libreria O365).

Non serve Outlook Desktop: il programma parla con Microsoft 365 via HTTPS e
funziona su qualsiasi sistema operativo. ``protocol`` descrive cio' che la
pipeline si aspetta, ``client`` lo realizza e ``poller`` esegue il controllo
periodico della posta in arrivo.
"""

from .protocol import MailClient, MailMessage

__all__ = ["MailClient", "MailMessage"]
