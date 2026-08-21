"""Interfaccia a riga di comando.

Quattro modi d'uso:

* ``authenticate`` - consenso una tantum all'applicazione: salva il token che
                     servira' a tutti gli avvii successivi;
* ``watch``        - controlla la casella ogni ``poll_interval_minutes`` e
                     tratta i messaggi non letti appena arrivati;
* ``run-once``     - esamina una sola volta i messaggi recenti (adatto anche a
                     un'attivita' pianificata o a un cron);
* ``check-file``   - prova OCR e regole su un file locale, senza toccare la
                     casella: e' il modo piu' rapido per verificare chiave API
                     e criteri.

Tutti i comandi girano su qualsiasi sistema operativo: l'accesso alla posta
avviene via Microsoft Graph, senza Outlook Desktop.
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .config import ConfigError, Settings
from .logging_setup import setup_logging
from .matching import evaluate
from .models import AttachmentFile, Decision
from .ocr.extractor import TextExtractor
from .ocr.ocrspace import OcrSpaceClient
from .outlook.client import OutlookError
from .pipeline import ForwardPipeline
from .state import ProcessedStore

logger = logging.getLogger("inoltro_email")

DEFAULT_CONFIG = Path("config.yaml")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="inoltro-email",
        description="Inoltra automaticamente le email Outlook i cui allegati "
                    "soddisfano i criteri configurati (lettura via ocr.space).",
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG,
                        help=f"percorso del file di configurazione (default: {DEFAULT_CONFIG})")
    parser.add_argument("--log-level", default=None,
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="sovrascrive logging.level della configurazione")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", dest="dry_run", action="store_true", default=None,
                       help="non invia nulla, mostra soltanto cosa verrebbe inoltrato")
    group.add_argument("--no-dry-run", dest="dry_run", action="store_false",
                       help="inoltra davvero i messaggi conformi")

    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("authenticate", help="autorizza l'applicazione e salva il token")
    sub.add_parser("watch", help="controlla la posta a intervalli regolari")

    run_once = sub.add_parser("run-once", help="esamina una volta i messaggi recenti")
    run_once.add_argument("--minutes", type=int, default=None,
                          help="finestra temporale da esaminare (default: outlook.catch_up_minutes)")
    run_once.add_argument("--include-read", action="store_true",
                          help="esamina anche i messaggi gia' letti (default: solo i non letti)")

    check = sub.add_parser("check-file", help="prova OCR e criteri su un file locale")
    check.add_argument("path", type=Path, help="PDF o immagine da analizzare")
    check.add_argument("--show-text", action="store_true", help="stampa il testo estratto")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        settings = Settings.load(args.config)
    except ConfigError as exc:
        print(f"Errore di configurazione: {exc}", file=sys.stderr)
        return 2

    if args.dry_run is not None:
        settings.forward.dry_run = args.dry_run
    settings.ensure_directories()
    started_at = datetime.now()
    log_file = setup_logging(
        args.log_level or settings.logging.level,
        settings.logging.file,
        per_session=settings.logging.per_session,
        keep_sessions=settings.logging.keep_sessions,
        started_at=started_at,
    )
    logger.info(
        "Sessione '%s' avviata il %s.", args.command, started_at.strftime("%d/%m/%Y alle %H:%M:%S")
    )
    if log_file:
        logger.info("Log di questa sessione: %s", log_file)

    try:
        if args.command == "check-file":
            return _cmd_check_file(settings, args.path, args.show_text)
        if args.command == "authenticate":
            return _cmd_authenticate(settings)
        if args.command == "run-once":
            return _cmd_run_once(settings, args.minutes, unread_only=not args.include_read)
        return _cmd_watch(settings)
    except KeyboardInterrupt:
        logger.info("Interrotto dall'utente.")
        return 130
    except OutlookError as exc:
        # Es. credenziali mancanti o token scaduto: il traceback non
        # aggiungerebbe nulla di utile a chi usa il programma.
        print(f"Errore Outlook: {exc}", file=sys.stderr)
        return 3


# ------------------------------------------------------------------ comandi


def _cmd_check_file(settings: Settings, path: Path, show_text: bool) -> int:
    """Analizza un singolo file locale: utile per tarare regole e chiave API."""
    if not path.is_file():
        print(f"File non trovato: {path}", file=sys.stderr)
        return 2

    attachment = AttachmentFile(path=path, original_name=path.name, size_bytes=path.stat().st_size)
    with OcrSpaceClient(settings.ocr) as ocr_client:
        extracted = TextExtractor(settings, ocr_client).extract(attachment)

    print(f"\nFile      : {path}")
    print(f"Sorgente  : {extracted.source.value}")
    if extracted.error:
        print(f"Errore    : {extracted.error}")
    if not extracted.ok:
        print("Esito     : testo non estratto, impossibile valutare i criteri.\n")
        return 1

    report = evaluate(extracted.text, settings.rules)
    print(f"Caratteri : {len(extracted.text)}")
    print(f"Criteri   : {report.summary()}")
    print(f"Esito     : {'CONFORME - la mail verrebbe inoltrata' if report.matched else 'non conforme'}\n")
    if show_text:
        print("--- testo estratto ---")
        print(extracted.text)
        print("--- fine testo ---\n")
    return 0 if report.matched else 1


def _cmd_authenticate(settings: Settings) -> int:
    """Consenso una tantum: apre l'URL di autorizzazione e salva il token."""
    from .outlook.client import OutlookClient

    client = OutlookClient(settings.outlook, settings.attachments.allowed_extensions)
    if not client.authenticate():
        print("Autenticazione non riuscita: nessun token salvato.", file=sys.stderr)
        return 3

    print(f"\nAutenticazione riuscita: token salvato in {settings.outlook.token_path}.")
    print("Da ora in poi 'watch' e 'run-once' partono senza chiedere nulla.\n")
    return 0


def _cmd_run_once(settings: Settings, minutes: Optional[int], unread_only: bool = True) -> int:
    window = minutes if minutes is not None else settings.outlook.catch_up_minutes
    with _build_context(settings) as (client, pipeline):
        results = pipeline.process_recent(window, unread_only=unread_only)

    forwarded = sum(1 for result in results if result.forwarded)
    errors = sum(1 for result in results if result.decision is Decision.ERROR)
    logger.info("Esaminati %d messaggi: %d inoltrati, %d errori.", len(results), forwarded, errors)
    return 1 if errors else 0


def _cmd_watch(settings: Settings) -> int:
    from .outlook.poller import watch

    with _build_context(settings) as (_client, pipeline):
        watch(settings, pipeline)
    return 0


# ------------------------------------------------------------------- setup


class _Context:
    """Costruisce e chiude in modo ordinato client di posta, OCR e store."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._ocr: Optional[OcrSpaceClient] = None
        self._store: Optional[ProcessedStore] = None

    def __enter__(self):
        from .outlook.client import OutlookClient

        client = OutlookClient(
            self._settings.outlook,
            allowed_extensions=self._settings.attachments.allowed_extensions,
        )
        client.connect()

        self._ocr = OcrSpaceClient(self._settings.ocr)
        self._store = ProcessedStore(self._settings.storage.db_path)
        pipeline = ForwardPipeline(
            settings=self._settings,
            mail_client=client,
            extractor=TextExtractor(self._settings, self._ocr),
            store=self._store,
        )
        return client, pipeline

    def __exit__(self, *_exc_info: object) -> None:
        if self._ocr is not None:
            self._ocr.close()
        if self._store is not None:
            self._store.close()


def _build_context(settings: Settings) -> _Context:
    return _Context(settings)


if __name__ == "__main__":
    raise SystemExit(main())
