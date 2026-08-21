"""Lettura del messaggio inviato da Power Automate.

Il flusso Power Automate ("Quando arriva un nuovo messaggio di posta
elettronica" oppure "Ottieni messaggio di posta elettronica") consegna una sola
email in JSON. Il formato cambia leggermente fra connettore Office 365 Outlook
e Microsoft Graph, quindi qui si accettano entrambe le forme:

    subject / Subject
    body / bodyHtml / bodyContent / bodyPreview, come stringa o {content, contentType}
    from  come stringa oppure {emailAddress: {address}}
    attachments[*].contentBytes / content / contentBase64 (base64)

Le foto incorporate nel corpo arrivano in due modi diversi e vengono
riconosciute entrambe: come allegati con ``isInline: true`` e come immagini
``<img src="data:image/png;base64,...">`` dentro l'HTML.

Un terzo modo lo usa il flusso in produzione: gli allegati vengono salvati in
una cartella e nel payload arriva soltanto il percorso, sotto la chiave
``attchment`` (scritta cosi', senza la "a")::

    "attchment":"C:\\Users\\user\\Documents\\Power Automate\\Allegati\\image.png"

Quei percorsi sono la base per l'OCR: il file viene letto da dove si trova e
mandato a ocr.space senza ricopiarlo.
"""

from __future__ import annotations

import base64
import binascii
import logging
import re
from html import unescape
from html.parser import HTMLParser
from pathlib import Path, PureWindowsPath
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .config import LocalFileSettings
from .models import InboundAttachment, InboundEmail, Origine

logger = logging.getLogger(__name__)

# Estensione da usare quando l'immagine del corpo non ha un nome file.
EXTENSION_BY_MIME = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/bmp": ".bmp",
    "image/tiff": ".tif",
    "application/pdf": ".pdf",
}

_DATA_URI = re.compile(r"^data:([\w./+-]+)?;base64,(.*)$", re.IGNORECASE | re.DOTALL)
_WHITESPACE = re.compile(r"[ \t\x0b\f\r\xa0]+")
_BLANK_LINES = re.compile(r"\n{3,}")
_LOOKS_LIKE_HTML = re.compile(r"<(?:html|body|div|p|br|table|span|img)\b", re.IGNORECASE)

# Tag che, chiudendosi, introducono un a capo nel testo semplice.
_BLOCK_TAGS = {
    "p", "div", "br", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6",
    "table", "ul", "ol", "blockquote", "section", "article", "header", "footer",
}
_SKIPPED_TAGS = {"script", "style", "head", "title"}

# Chiavi sotto cui il flusso puo' mandare i percorsi degli allegati salvati su
# disco. "attchment" e' scritto cosi' nel flusso attuale: si accetta com'e'.
PATH_KEYS = ("attchment", "attachment", "attachmentPath", "attachmentPaths",
             "allegato", "allegati", "percorso", "percorsi", "filePath")

# Il flusso, quando non riesce a risolvere un'espressione, manda il testo
# dell'errore al posto del corpo: va segnalato, non analizzato.
_UNRESOLVED_BODY = re.compile(
    r"^\s*(unknown property|expression evaluation failed|invalidtemplate)\b",
    re.IGNORECASE,
)


class InboundError(ValueError):
    """Payload non interpretabile: manca un campo o il base64 e' rotto."""


def parse_email(
    payload: Any,
    *,
    include_inline_images: bool = True,
    max_attachment_bytes: Optional[int] = None,
    local_files: Optional[LocalFileSettings] = None,
) -> InboundEmail:
    """Costruisce un ``InboundEmail`` dal JSON ricevuto da Power Automate.

    ``local_files`` abilita e delimita la lettura degli allegati indicati per
    percorso; se non viene passato si usano le impostazioni predefinite.
    """
    if not isinstance(payload, Mapping):
        raise InboundError("Il corpo della richiesta deve essere un oggetto JSON.")

    warnings: List[str] = []
    data = _CaseInsensitive(payload)
    body_raw, is_html = _read_body(data)

    if is_html:
        body_text, embedded = _parse_html_body(body_raw)
        body_html = body_raw
    else:
        body_text, embedded = _clean_text(body_raw), []
        body_html = ""

    subject = _as_text(data.get("subject"))
    if not subject and not body_text.strip():
        raise InboundError("Il messaggio non contiene ne' oggetto ne' corpo: nulla da analizzare.")

    if _UNRESOLVED_BODY.match(body_text):
        # Es. "Unknown Property 'HtmlBody'": il corpo non e' arrivato. Si
        # analizza comunque l'oggetto, ma il flusso va corretto a monte.
        warnings.append(
            f"Corpo non risolto dal flusso Power Automate ({body_text.strip()[:80]}): "
            "l'analisi si basa solo su oggetto e allegati."
        )
        logger.warning("Corpo non risolto dal flusso: %s", body_text.strip()[:120])
        body_text = ""

    attachments = _read_attachments(
        data.get("attachments"),
        include_inline_images=include_inline_images,
        max_attachment_bytes=max_attachment_bytes,
    )
    attachments.extend(
        _read_path_attachments(
            data,
            settings=local_files or LocalFileSettings(),
            max_attachment_bytes=max_attachment_bytes,
            warnings=warnings,
        )
    )
    if include_inline_images:
        attachments.extend(
            item for item in embedded
            if max_attachment_bytes is None or item.size_bytes <= max_attachment_bytes
        )

    return InboundEmail(
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        message_id=_as_text(data.get("id") or data.get("messageId")),
        internet_message_id=_as_text(data.get("internetMessageId") or data.get("messageId")),
        sender=_read_sender(data),
        received_at=_as_text(
            data.get("receivedDateTime") or data.get("received") or data.get("date")
        ),
        attachments=attachments,
        warnings=warnings,
    )


# --------------------------------------------------------------------- corpo


def html_to_text(html: str) -> str:
    """Riduce l'HTML del corpo a testo semplice, mantenendo gli a capo."""
    return _parse_html_body(html)[0]


def _parse_html_body(html: str) -> Tuple[str, List[InboundAttachment]]:
    parser = _BodyParser()
    try:
        parser.feed(html)
        parser.close()
    except Exception as exc:  # noqa: BLE001 - HTML malformato: si usa cio' che si e' letto
        logger.warning("Corpo HTML malformato, lettura parziale: %s", exc)

    images: List[InboundAttachment] = []
    for index, source in enumerate(parser.image_sources, start=1):
        image = _from_data_uri(source, index)
        if image is not None:
            images.append(image)
    return _clean_text(parser.text()), images


class _BodyParser(HTMLParser):
    """Estrae testo e sorgenti delle immagini da un corpo HTML."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: List[str] = []
        self._skip_depth = 0
        self.image_sources: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if tag in _SKIPPED_TAGS:
            self._skip_depth += 1
            return
        if tag == "img":
            source = dict(attrs).get("src") or ""
            if source:
                self.image_sources.append(source)
            # L'attributo alt e' spesso l'unico testo di un'immagine firmata.
            alt = dict(attrs).get("alt") or ""
            if alt:
                self._chunks.append(f" {alt} ")
        if tag in _BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_startendtag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIPPED_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if tag in _BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            self._chunks.append(data)

    def text(self) -> str:
        return "".join(self._chunks)


def _clean_text(text: str) -> str:
    """Normalizza spazi e a capo: il testo va poi a regole e sentiment."""
    if not text:
        return ""
    text = unescape(text).replace("\r\n", "\n").replace("\r", "\n")
    text = _WHITESPACE.sub(" ", text)
    lines = [line.strip() for line in text.split("\n")]
    return _BLANK_LINES.sub("\n\n", "\n".join(lines)).strip()


def _read_body(data: "_CaseInsensitive") -> Tuple[str, bool]:
    """Restituisce (corpo, e_html) qualunque sia la forma del payload."""
    for key in ("body", "bodyHtml", "bodyContent", "bodyPreview"):
        value = data.get(key)
        if isinstance(value, Mapping):
            inner = _CaseInsensitive(value)
            content = _as_text(inner.get("content") or inner.get("value"))
            content_type = _as_text(inner.get("contentType") or inner.get("type")).lower()
            if content:
                return content, ("html" in content_type or _looks_like_html(content))
        elif isinstance(value, str) and value.strip():
            return value, _is_html_flagged(data, key, value)
    return "", False


def _is_html_flagged(data: "_CaseInsensitive", key: str, content: str) -> bool:
    """Il corpo va trattato come HTML?

    Si guarda prima il campo dichiarato dal flusso, ma un corpo pieno di tag
    viene ripulito comunque: alcuni flussi lasciano ``isHtml`` a false e
    lasciare i tag nel testo falserebbe criteri e sentiment.
    """
    for flag_key in ("isHtml", "bodyType", "contentType", "bodyContentType"):
        flag = data.get(flag_key)
        if isinstance(flag, bool) and flag:
            return True
        if isinstance(flag, str) and flag.strip() and "html" in flag.lower():
            return True
    return key == "bodyHtml" or _looks_like_html(content)


def _looks_like_html(content: str) -> bool:
    return bool(_LOOKS_LIKE_HTML.search(content))


# ------------------------------------------------------------------ allegati


def _read_attachments(
    raw: Any,
    *,
    include_inline_images: bool,
    max_attachment_bytes: Optional[int],
) -> List[InboundAttachment]:
    if raw in (None, ""):
        return []
    if isinstance(raw, Mapping):  # un solo allegato non incapsulato in una lista
        raw = [raw]
    if not isinstance(raw, list):
        raise InboundError("Il campo 'attachments' deve essere un elenco di allegati.")

    attachments: List[InboundAttachment] = []
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, Mapping):
            logger.warning("Allegato %d ignorato: non e' un oggetto JSON.", index)
            continue
        entry = _CaseInsensitive(item)

        content_b64 = ""
        for key in ("contentBytes", "content", "contentBase64", "$content"):
            value = entry.get(key)
            if isinstance(value, str) and value.strip():
                content_b64 = value
                break
        if not content_b64:
            logger.warning("Allegato '%s' senza contenuto base64, ignorato.",
                           _as_text(entry.get("name")) or index)
            continue

        inline = _is_inline(entry)
        if inline and not include_inline_images:
            logger.debug("Immagine incorporata ignorata per configurazione.")
            continue

        content_type = _as_text(entry.get("contentType") or entry.get("mimeType"))
        try:
            content = decode_base64(content_b64)
        except InboundError as exc:
            logger.warning("Allegato '%s' non decodificabile: %s", entry.get("name"), exc)
            continue

        if max_attachment_bytes is not None and len(content) > max_attachment_bytes:
            logger.info("Allegato '%s' oltre il limite di %d byte, ignorato.",
                        entry.get("name"), max_attachment_bytes)
            continue

        name = _as_text(entry.get("name") or entry.get("fileName"))
        attachments.append(
            InboundAttachment(
                name=_ensure_name(name, content_type, index, inline),
                content=content,
                content_type=content_type,
                origine=Origine.CORPO if inline else Origine.ALLEGATO,
            )
        )
    return attachments


# --------------------------------------------- allegati indicati per percorso


def _read_path_attachments(
    data: "_CaseInsensitive",
    *,
    settings: LocalFileSettings,
    max_attachment_bytes: Optional[int],
    warnings: List[str],
) -> List[InboundAttachment]:
    """Legge gli allegati che il payload indica solo con il percorso su disco."""
    raw_values: List[Any] = []
    for key in PATH_KEYS:
        value = data.get(key)
        if value not in (None, "", []):
            raw_values.append(value)
    if not raw_values:
        return []

    candidates = _split_paths(raw_values)
    if not candidates:
        return []

    if not settings.enabled:
        message = (
            f"{len(candidates)} allegato/i indicato/i per percorso non letto/i: "
            "lettura dei file locali disattivata (local_files.enabled)."
        )
        logger.info(message)
        warnings.append(message)
        return []

    attachments: List[InboundAttachment] = []
    for raw_path in candidates:
        resolved, problem = _resolve_local_path(raw_path, settings)
        if resolved is None:
            logger.warning("Allegato '%s' non leggibile: %s", raw_path, problem)
            warnings.append(f"Allegato '{raw_path}' non letto: {problem}.")
            continue

        size = resolved.stat().st_size
        if max_attachment_bytes is not None and size > max_attachment_bytes:
            message = f"{size} byte oltre il limite di {max_attachment_bytes}"
            logger.info("Allegato '%s' ignorato: %s.", resolved, message)
            warnings.append(f"Allegato '{resolved.name}' non letto: {message}.")
            continue

        logger.info("Allegato da percorso: %s (%d byte).", resolved, size)
        attachments.append(
            InboundAttachment(
                name=resolved.name,
                content_type="",
                origine=Origine.ALLEGATO,
                source_path=resolved,
            )
        )
    return attachments


def _split_paths(values: Sequence[Any]) -> List[str]:
    """Appiattisce elenchi e stringhe multiriga in un elenco di percorsi."""
    paths: List[str] = []
    for value in _flatten(values):
        text = _as_text(value)
        if not text:
            continue
        for line in text.replace("\r\n", "\n").split("\n"):
            candidate = line.strip().strip('"').strip("'").rstrip(";").strip()
            if candidate and candidate not in paths:
                paths.append(candidate)
    return paths


def _flatten(values: Iterable[Any]) -> Iterable[Any]:
    for value in values:
        if isinstance(value, (list, tuple)):
            yield from _flatten(value)
        else:
            yield value


def _resolve_local_path(
    raw_path: str,
    settings: LocalFileSettings,
) -> Tuple[Optional[Path], str]:
    """Trova il file indicato dal payload; ``(None, motivo)`` se non ci riesce.

    Il percorso arriva nella forma Windows del flusso. Si prova prima cosi'
    com'e' (servizio e flusso sulla stessa macchina, il caso normale), poi si
    cerca il file per nome nelle cartelle configurate: cosi' lo stesso payload
    funziona anche se il servizio gira altrove.
    """
    candidate = Path(raw_path)
    filename = PureWindowsPath(raw_path).name or candidate.name

    found: Optional[Path] = None
    try:
        if candidate.is_file():
            found = candidate
    except OSError as exc:  # percorso non valido per il sistema operativo locale
        logger.debug("Percorso '%s' non utilizzabile su questo sistema: %s", raw_path, exc)

    if found is None and filename:
        for directory in settings.search_directories:
            alternative = Path(directory) / filename
            if alternative.is_file():
                logger.info("'%s' ritrovato in %s.", filename, directory)
                found = alternative
                break

    if found is None:
        return None, "file non trovato sul disco del servizio"

    try:
        resolved = found.resolve()
    except OSError as exc:
        return None, f"percorso non risolvibile ({exc})"

    if settings.allowed_directories and not _inside_any(resolved, settings.allowed_directories):
        return None, "percorso fuori dalle cartelle consentite (local_files.allowed_directories)"
    return resolved, ""


def _inside_any(path: Path, directories: Sequence[Path]) -> bool:
    for directory in directories:
        try:
            path.relative_to(Path(directory).resolve())
            return True
        except (ValueError, OSError):
            continue
    return False


def _is_inline(entry: "_CaseInsensitive") -> bool:
    flag = entry.get("isInline")
    if isinstance(flag, bool):
        return flag
    if isinstance(flag, str):
        return flag.strip().lower() in ("true", "1", "si", "yes")
    return bool(_as_text(entry.get("contentId")))


def _from_data_uri(source: str, index: int) -> Optional[InboundAttachment]:
    """Converte un ``<img src="data:image/png;base64,...">`` in allegato."""
    match = _DATA_URI.match(source.strip())
    if not match:
        return None  # immagine remota (http/cid): non e' scaricabile da qui
    mime = (match.group(1) or "image/png").lower()
    try:
        content = decode_base64(match.group(2))
    except InboundError as exc:
        logger.warning("Immagine nel corpo non decodificabile: %s", exc)
        return None
    if not content:
        return None
    return InboundAttachment(
        name=f"corpo-{index}{EXTENSION_BY_MIME.get(mime, '.png')}",
        content=content,
        content_type=mime,
        origine=Origine.CORPO,
    )


def decode_base64(value: str) -> bytes:
    """Decodifica tollerante: accetta a capo, spazi e padding mancante."""
    cleaned = re.sub(r"\s+", "", value)
    if cleaned.startswith("data:"):
        match = _DATA_URI.match(cleaned)
        cleaned = match.group(2) if match else ""
    padding = (-len(cleaned)) % 4
    try:
        return base64.b64decode(cleaned + "=" * padding, validate=False)
    except (binascii.Error, ValueError) as exc:
        raise InboundError(f"contenuto base64 non valido: {exc}") from exc


def _ensure_name(name: str, content_type: str, index: int, inline: bool) -> str:
    """Garantisce un nome con estensione: serve a scegliere come leggerlo."""
    name = (name or "").strip().replace("\n", " ")
    prefix = "corpo" if inline else "allegato"
    if not name:
        name = f"{prefix}-{index}"
    if "." not in name:
        mime = content_type.split(";")[0].strip().lower()
        name += EXTENSION_BY_MIME.get(mime, "")
    return name


# --------------------------------------------------------------------- utili


def _read_sender(data: "_CaseInsensitive") -> str:
    for key in ("from", "sender", "fromAddress"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, Mapping):
            inner = _CaseInsensitive(value)
            address = inner.get("emailAddress")
            if isinstance(address, Mapping):
                inner = _CaseInsensitive(address)
            found = _as_text(inner.get("address") or inner.get("name"))
            if found:
                return found
    return ""


def _as_text(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list)):
        return ""
    return str(value).strip()


class _CaseInsensitive:
    """Accesso a un dizionario JSON ignorando maiuscole e minuscole.

    Power Automate usa ``subject``/``body``, Graph a volte ``Subject``: cosi'
    il servizio accetta entrambe le convenzioni senza duplicare i controlli.
    """

    def __init__(self, data: Mapping[str, Any]) -> None:
        self._data: Dict[str, Any] = dict(data)
        self._lower = {str(key).lower(): value for key, value in self._data.items()}

    def get(self, key: str, default: Any = None) -> Any:
        if key in self._data:
            return self._data[key]
        return self._lower.get(key.lower(), default)
