"""Interfaccia a riga di comando.

Tre modi d'uso:

* ``serve``      - avvia il servizio HTTP che Power Automate interroga;
* ``analizza``   - analizza un payload JSON gia' salvato su file (o letto da
                   standard input): e' il modo piu' rapido per provare regole e
                   punteggi senza far partire il server;
* ``check-file`` - prova OCR e criteri su un singolo PDF o immagine, senza
                   passare da un'email.

Tutti i comandi girano su qualsiasi sistema operativo: non serve Outlook, la
posta arriva dal flusso Power Automate.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .analysis import EmailAnalyzer
from .api.responses import analysis_to_dict
from .config import ConfigError, Settings
from .inbound import InboundError, parse_email
from .rawjson import RawJsonError, loads_tolerant
from .logging_setup import setup_logging
from .matching import evaluate
from .models import AttachmentFile, Esito
from .ocr.extractor import TextExtractor
from .ocr.ocrspace import OcrSpaceClient

logger = logging.getLogger("inoltro_email")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="inoltro-email",
        description="Servizio HTTP che analizza le email di telemedicina "
                    "inviate da Power Automate (screening, OCR, sentiment).",
    )
    parser.add_argument("--config", type=Path, default=None,
                        help="percorso del file di configurazione (default: config.yaml se esiste)")
    parser.add_argument("--log-level", default=None,
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="sovrascrive logging.level della configurazione")

    sub = parser.add_subparsers(dest="command", required=True)

    serve = sub.add_parser("serve", help="avvia il servizio HTTP")
    serve.add_argument("--host", default=None, help="indirizzo di ascolto (default: api.host)")
    serve.add_argument("--port", type=int, default=None, help="porta di ascolto (default: api.port)")
    serve.add_argument("--reload", action="store_true",
                       help="ricarica automaticamente al cambiare del codice (sviluppo)")

    analizza = sub.add_parser("analizza", help="analizza un payload JSON di Power Automate")
    analizza.add_argument("path", type=Path, nargs="?", default=None,
                          help="file JSON da analizzare ('-' o assente: standard input)")

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

    if args.command == "serve":
        if args.host:
            settings.api.host = args.host
        if args.port:
            settings.api.port = args.port

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
        if args.command == "serve":
            return _cmd_serve(settings, reload=args.reload)
        if args.command == "analizza":
            return _cmd_analizza(settings, args.path)
        return _cmd_check_file(settings, args.path, args.show_text)
    except KeyboardInterrupt:
        logger.info("Interrotto dall'utente.")
        return 130


# ------------------------------------------------------------------ comandi


def _cmd_serve(settings: Settings, *, reload: bool = False) -> int:
    from .api.server import run

    run(settings, reload=reload)
    return 0


def _cmd_analizza(settings: Settings, path: Optional[Path]) -> int:
    """Analizza un payload salvato su file: stessa risposta dell'endpoint HTTP."""
    try:
        raw = sys.stdin.read() if path is None or str(path) == "-" else path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"File non leggibile: {exc}", file=sys.stderr)
        return 2

    try:
        payload, repairs = loads_tolerant(raw)
    except RawJsonError as exc:
        print(f"JSON non valido: {exc}", file=sys.stderr)
        return 2

    if repairs:
        print(f"JSON riparato in lettura: {'; '.join(repairs)}", file=sys.stderr)

    try:
        email = parse_email(
            payload,
            include_inline_images=settings.attachments.include_inline_images,
            max_attachment_bytes=settings.attachments.max_bytes,
            local_files=settings.local_files,
        )
    except InboundError as exc:
        print(f"Payload non interpretabile: {exc}", file=sys.stderr)
        return 2

    if repairs:
        email.warnings.append("JSON non valido riparato in lettura: " + "; ".join(repairs))

    with OcrSpaceClient(settings.ocr) as ocr_client:
        analyzer = EmailAnalyzer(settings, TextExtractor(settings, ocr_client))
        analysis = analyzer.analyze(email)

    print(json.dumps(
        analysis_to_dict(
            analysis,
            include_text=settings.attachments.return_text,
            max_text_chars=settings.attachments.max_text_chars,
        ),
        indent=2, ensure_ascii=False,
    ))
    # L'esito e' nel JSON: il codice di uscita segnala solo se l'analisi si e'
    # interrotta, non se l'email era conforme.
    return 1 if analysis.esito is Esito.ERRORE else 0


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
    print(f"Esito     : {'CONFORME' if report.matched else 'non conforme'}\n")
    if show_text:
        print("--- testo estratto ---")
        print(extracted.text)
        print("--- fine testo ---\n")
    return 0 if report.matched else 1


if __name__ == "__main__":
    raise SystemExit(main())
