"""Lettura tollerante del JSON inviato da Power Automate.

Il flusso costruisce il corpo della richiesta concatenando stringhe, non
serializzando un oggetto: il risultato e' quasi sempre un JSON *non valido*.
Nei log del servizio si vedono tre guasti ricorrenti, tutti nello stesso
payload::

    {"subject":"...","body":"<html>
    <head>
    <style type="text/css"> P {margin-top:0;} </style>
    ...","date":"08/20/2026 10:26","attchment":"C:\\Users\\user\\Allegati\\image.png"}

1. **caratteri di controllo**: l'HTML del corpo viene inserito con gli a capo
   veri, mentre JSON li vuole scritti ``\\n``
   (*Invalid control character at: line 1 column 133*);
2. **virgolette non protette**: ``<style type="text/css">`` chiude la stringa a
   meta' (*Expecting ',' delimiter: line 1 column 84*), e lo stesso vale per un
   oggetto come ``Lettura "Mario Carrara": Gramsci``;
3. **percorsi Windows**: ``C:\\Users\\...`` contiene ``\\U``, ``\\D``, ``\\P``,
   che per JSON sono sequenze di escape inesistenti.

A questi si aggiunge il caso di piu' allegati, che il flusso scrive come valori
affiancati senza chiave (``"attchment":"primo.pdf","secondo.pdf"``).

Questo modulo prova prima ``json.loads`` (la strada veloce: se il flusso viene
corretto a monte non si paga nulla) e solo in caso di errore rilegge il testo
con un parser indulgente, che ricostruisce l'oggetto e riporta l'elenco delle
riparazioni applicate. Le riparazioni finiscono nei log e nella risposta: il
payload viene accettato, ma resta visibile che era da aggiustare.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

# Sequenze di escape previste da JSON dopo una barra rovesciata.
_SIMPLE_ESCAPES = {
    '"': '"', "\\": "\\", "/": "/",
    "b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t",
}
_HEX_DIGITS = frozenset("0123456789abcdefABCDEF")
_WHITESPACE = " \t\n\r\f\v"

# Dopo la chiusura di una stringa-valore ci si aspetta la fine del contenitore
# oppure una virgola seguita dall'inizio di un altro elemento.
_VALUE_FOLLOWERS = frozenset('}]')
_ELEMENT_STARTS = frozenset('"{[')
_LITERAL_STARTS = frozenset("-0123456789tfn")


class RawJsonError(ValueError):
    """Il payload non e' interpretabile nemmeno con le riparazioni."""


def loads_tolerant(raw: Any) -> Tuple[Any, List[str]]:
    """Interpreta ``raw`` restituendo ``(valore, riparazioni)``.

    ``riparazioni`` e' vuoto quando il payload era gia' JSON valido. Solleva
    ``RawJsonError`` solo se non si riesce a ricavare nulla di sensato.
    """
    text = _as_text(raw)
    if not text.strip():
        raise RawJsonError("corpo della richiesta vuoto")

    try:
        return json.loads(text), []
    except ValueError as exc:
        first_error = str(exc)

    parser = _TolerantParser(text)
    try:
        value = parser.parse()
    except Exception as exc:  # noqa: BLE001 - qualunque intoppo diventa un errore leggibile
        raise RawJsonError(f"{first_error} (riparazione non riuscita: {exc})") from exc

    if not _has_content(value):
        # Dalla riparazione non e' uscito nulla di utile: era spazzatura, non
        # un payload da aggiustare. Meglio l'errore originale di un oggetto
        # vuoto analizzato come se fosse una email.
        raise RawJsonError(first_error)
    return value, parser.repairs


def _has_content(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (dict, list, str)):
        return bool(value if not isinstance(value, str) else value.strip())
    return True


def _as_text(raw: Any) -> str:
    if isinstance(raw, str):
        return raw.lstrip("\ufeff")
    if isinstance(raw, (bytes, bytearray)):
        return bytes(raw).decode("utf-8", errors="replace").lstrip("\ufeff")
    raise RawJsonError(f"atteso testo JSON, ricevuto {type(raw).__name__}")


class _TolerantParser:
    """Parser a discesa ricorsiva che non si ferma davanti agli errori tipici.

    Le regole in piu' rispetto a JSON sono poche e mirate ai guasti osservati:
    una virgoletta chiude la stringa solo se cio' che segue e' davvero la fine
    del valore, i caratteri di controllo e le barre rovesciate isolate vengono
    presi alla lettera, e piu' valori affiancati sotto la stessa chiave
    diventano un elenco.
    """

    def __init__(self, text: str) -> None:
        self._text = text
        self._pos = 0
        # Le riparazioni si ripetono a decine (un a capo per riga di HTML):
        # si contano invece di elencarle una per una.
        self._repairs: Dict[str, int] = {}

    # ------------------------------------------------------------- risultato

    @property
    def repairs(self) -> List[str]:
        """Riparazioni applicate, con il numero di occorrenze."""
        return [
            label if count == 1 else f"{label} (x{count})"
            for label, count in self._repairs.items()
        ]

    def parse(self) -> Any:
        self._skip_whitespace()
        value = self._parse_value(in_array=False)
        self._skip_whitespace()
        if self._pos < len(self._text):
            self._note("testo in eccesso dopo la fine del JSON, ignorato")
        return value

    # --------------------------------------------------------------- valori

    def _parse_value(self, *, in_array: bool) -> Any:
        self._skip_whitespace()
        char = self._peek()
        if char == "{":
            return self._parse_object()
        if char == "[":
            return self._parse_array()
        if char == '"':
            return self._parse_string(mode="value", in_array=in_array)
        return self._parse_literal()

    def _parse_object(self) -> Dict[str, Any]:
        self._pos += 1  # graffa aperta
        result: Dict[str, Any] = {}
        last_key: Optional[str] = None

        while True:
            self._skip_whitespace()
            char = self._peek()
            if not char:
                self._note("oggetto non chiuso alla fine del payload")
                return result
            if char == "}":
                self._pos += 1
                return result
            if char == ",":
                self._pos += 1
                continue

            key = self._parse_key()
            if key is None:
                # Non e' una chiave: e' un valore affiancato al precedente,
                # come accade con piu' allegati ("attchment":"a.pdf","b.pdf").
                value = self._parse_value(in_array=False)
                if last_key is None:
                    self._note("valore senza chiave, ignorato")
                    continue
                result[last_key] = _as_list(result.get(last_key)) + _as_list(value)
                self._note(f"piu' valori per la chiave '{last_key}', raccolti in elenco")
                continue

            self._skip_whitespace()
            if self._peek() == ":":
                self._pos += 1
            else:
                self._note(f"manca ':' dopo la chiave '{key}'")
            result[key] = self._parse_value(in_array=False)
            last_key = key

    def _parse_array(self) -> List[Any]:
        self._pos += 1  # quadra aperta
        items: List[Any] = []

        while True:
            self._skip_whitespace()
            char = self._peek()
            if not char:
                self._note("elenco non chiuso alla fine del payload")
                return items
            if char == "]":
                self._pos += 1
                return items
            if char == ",":
                self._pos += 1
                continue
            items.append(self._parse_value(in_array=True))

    def _parse_key(self) -> Optional[str]:
        """Legge una chiave, oppure restituisce None senza consumare nulla.

        Serve a distinguere ``"attchment":"a.pdf"`` (chiave) da ``"b.pdf"``
        affiancato al valore precedente: si prova a leggere la stringa e si
        guarda se dopo c'e' i due punti.
        """
        if self._peek() != '"':
            return None

        saved_pos = self._pos
        saved_repairs = dict(self._repairs)
        candidate = self._parse_string(mode="key", in_array=False)
        self._skip_whitespace()
        if self._peek() == ":":
            return candidate

        self._pos = saved_pos
        self._repairs = saved_repairs
        return None

    def _parse_literal(self) -> Any:
        """Numeri, ``true``/``false``/``null`` e valori scritti senza virgolette."""
        start = self._pos
        while self._pos < len(self._text) and self._text[self._pos] not in ",}]":
            self._pos += 1
        token = self._text[start:self._pos].strip()
        if not token:
            self._note("valore mancante")
            return None
        try:
            return json.loads(token)
        except ValueError:
            self._note("valore senza virgolette, letto come testo")
            return token

    # -------------------------------------------------------------- stringhe

    def _parse_string(self, *, mode: str, in_array: bool) -> str:
        self._pos += 1  # virgoletta iniziale
        chunks: List[str] = []

        while True:
            char = self._peek()
            if not char:
                self._note("stringa non chiusa alla fine del payload")
                break
            if char == "\\":
                chunks.append(self._read_escape())
                continue
            if char == '"':
                if self._closes_string(mode=mode, in_array=in_array):
                    self._pos += 1
                    break
                # Virgoletta interna al testo: tipica degli attributi HTML
                # (style="...") e dei titoli fra virgolette nell'oggetto.
                self._note("virgolette non protette dentro una stringa")
                chunks.append('"')
                self._pos += 1
                continue
            if char < " ":
                # A capo e tabulazioni inseriti cosi' come sono nel corpo HTML.
                self._note("carattere di controllo dentro una stringa")
                chunks.append(char)
                self._pos += 1
                continue
            chunks.append(char)
            self._pos += 1

        return "".join(chunks)

    def _closes_string(self, *, mode: str, in_array: bool) -> bool:
        """La virgoletta corrente chiude davvero la stringa?"""
        char, position = self._next_significant(self._pos + 1)
        if not char:
            return True
        if mode == "key":
            # Una chiave finisce con ``":``; le altre chiusure servono a
            # riconoscere che la stringa non era affatto una chiave.
            return char in ":,}]"
        if char in _VALUE_FOLLOWERS:
            return True
        if char == ",":
            following, _ = self._next_significant(position + 1)
            if not following or following in _ELEMENT_STARTS or following in _VALUE_FOLLOWERS:
                return True
            return in_array and following in _LITERAL_STARTS
        return False

    def _read_escape(self) -> str:
        """Legge una sequenza di escape, tollerando quelle inesistenti."""
        following = self._peek(1)
        if following == "u":
            digits = self._text[self._pos + 2:self._pos + 6]
            if len(digits) == 4 and all(digit in _HEX_DIGITS for digit in digits):
                self._pos += 6
                return chr(int(digits, 16))
            # Non e' un carattere unicode ma un percorso: "C:\Users\user\...".
        elif following in _SIMPLE_ESCAPES:
            self._pos += 2
            return _SIMPLE_ESCAPES[following]

        # Percorso Windows: "C:\Users\..." - la barra e' un carattere del testo.
        self._note("barra rovesciata non valida (percorso Windows), letta come carattere")
        self._pos += 1
        return "\\"

    # ----------------------------------------------------------------- utili

    def _peek(self, offset: int = 0) -> str:
        index = self._pos + offset
        return self._text[index] if index < len(self._text) else ""

    def _skip_whitespace(self) -> None:
        while self._pos < len(self._text) and self._text[self._pos] in _WHITESPACE:
            self._pos += 1

    def _next_significant(self, start: int) -> Tuple[str, int]:
        """Primo carattere non bianco da ``start``, con la sua posizione."""
        index = start
        while index < len(self._text) and self._text[index] in _WHITESPACE:
            index += 1
        if index >= len(self._text):
            return "", index
        return self._text[index], index

    def _note(self, label: str) -> None:
        self._repairs[label] = self._repairs.get(label, 0) + 1


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    return [value]
