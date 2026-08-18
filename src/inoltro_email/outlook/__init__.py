"""Integrazione con Outlook Desktop tramite COM (solo Windows).

I moduli ``protocol`` e ``client`` sono importabili anche fuori da Windows:
``win32com`` viene importato solo al momento della connessione, cosi' i test
della pipeline girano ovunque usando un client fittizio.
"""

from .protocol import MailClient, MailMessage

__all__ = ["MailClient", "MailMessage"]
