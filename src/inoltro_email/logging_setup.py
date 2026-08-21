"""Configurazione del logging: console + un file nuovo per ogni sessione.

Ogni avvio del programma scrive il proprio file di log, il cui nome porta la
data e l'ora di inizio (``logs/inoltro-20250521-091500.log``): i registri di
esecuzioni diverse non si mescolano piu' e ritrovare cosa e' successo in un
determinato avvio e' immediato. I file piu' vecchi vengono cancellati quando
superano il numero indicato da ``logging.keep_sessions``.
"""

from __future__ import annotations

import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)-28s %(message)s"
# Ordinabile alfabeticamente = ordinabile cronologicamente.
SESSION_STAMP_FORMAT = "%Y%m%d-%H%M%S"
# Riconosce i soli file generati da noi: la pulizia non tocca nient'altro.
SESSION_STAMP_PATTERN = re.compile(r"-\d{8}-\d{6}(-\d+)?$")
DEFAULT_KEEP_SESSIONS = 30


def session_log_path(base_file: Path, started_at: Optional[datetime] = None) -> Path:
    """Da ``logs/inoltro.log`` a ``logs/inoltro-<data>-<ora>.log``.

    Se due sessioni partono nello stesso secondo si aggiunge un progressivo,
    cosi' ognuna conserva il proprio file.
    """
    base_file = Path(base_file)
    stamp = (started_at or datetime.now()).strftime(SESSION_STAMP_FORMAT)
    candidate = base_file.with_name(f"{base_file.stem}-{stamp}{base_file.suffix}")
    counter = 1
    while candidate.exists():
        candidate = base_file.with_name(f"{base_file.stem}-{stamp}-{counter}{base_file.suffix}")
        counter += 1
    return candidate


def prune_session_logs(base_file: Path, keep: int = DEFAULT_KEEP_SESSIONS) -> List[Path]:
    """Tiene i ``keep`` file di sessione piu' recenti, elimina gli altri.

    Con ``keep <= 0`` non si cancella nulla. Restituisce i file rimossi.
    """
    if keep <= 0:
        return []

    base_file = Path(base_file)
    existing = sorted(
        path
        for path in base_file.parent.glob(f"{base_file.stem}-*{base_file.suffix}")
        if path.is_file() and SESSION_STAMP_PATTERN.search(path.stem)
    )

    removed: List[Path] = []
    for path in existing[: max(0, len(existing) - keep)]:
        try:
            path.unlink()
        except OSError:  # file in uso o permessi: non e' un motivo per fermarsi
            continue
        removed.append(path)
    return removed


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    *,
    per_session: bool = True,
    keep_sessions: int = DEFAULT_KEEP_SESSIONS,
    started_at: Optional[datetime] = None,
) -> Optional[Path]:
    """Installa gli handler sul logger radice (idempotente).

    Restituisce il file effettivamente scritto, ``None`` se si logga solo a
    console. Con ``per_session`` disattivato si continua a scrivere sempre sullo
    stesso file indicato dalla configurazione.
    """
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    for handler in list(root.handlers):
        root.removeHandler(handler)
        handler.close()

    formatter = logging.Formatter(LOG_FORMAT)

    # I log vanno su stderr, non su stdout: il comando "analizza" stampa il
    # JSON del verdetto su stdout, e con i due flussi mescolati non si puo'
    # redirigere il risultato in un file. Ora ogni allegato passa dall'OCR e i
    # log sono parecchi, quindi la distinzione conta.
    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(formatter)
    root.addHandler(console)

    active_file: Optional[Path] = None
    if log_file:
        base_file = Path(log_file)
        base_file.parent.mkdir(parents=True, exist_ok=True)
        started_at = started_at or datetime.now()

        active_file = session_log_path(base_file, started_at) if per_session else base_file

        file_handler = logging.FileHandler(active_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

        if per_session:
            # Dopo aver aperto il file della sessione in corso: e' il piu'
            # recente, quindi rientra sempre fra quelli conservati.
            prune_session_logs(base_file, keep_sessions)

    # urllib3 logga ogni connessione a livello DEBUG: troppo rumoroso.
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    return active_file
