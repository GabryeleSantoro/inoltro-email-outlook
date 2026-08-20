"""Percentuale di sicurezza: e' telemedicina? e' una prenotazione?

Il servizio non deve piu' rispondere solo "si"/"no". Restituisce due
percentuali distinte, entrambe spiegabili:

* **telemedicina** - quanto e' sicuro che il messaggio riguardi la
  telemedicina (televisita, teleconsulto, telemonitoraggio, teleassistenza);
* **prenotazione** - quanto e' sicuro che riguardi *la prenotazione* di una
  prestazione di telemedicina, che e' cosa diversa dal semplice parlarne.

La distinzione nasce dai messaggi realmente ricevuti: nella posta arrivano
fogli di accessi mensili ("ACCESSI IN TELEMEDICINA_Maggio 2026.xlsx"),
variazioni economiche, preventivi di fornitori, richieste di apertura agenda e
segnalazioni di malfunzionamento. Parlano tutti di telemedicina, nessuno e' una
prenotazione: la sola presenza della parola non basta come verdetto.

Come si calcola
---------------
Ogni indizio vale un peso in *log-odds*: positivo se depone a favore, negativo
se depone contro. I pesi si sommano a un termine costante e la somma passa per
una funzione logistica, che la riporta fra 0 e 100. Vantaggi rispetto a una
somma di percentuali: gli indizi si accumulano senza mai sfondare il 100%, un
indizio contrario puo' annullarne uno a favore, e ogni contributo resta
leggibile nella risposta (``indizi``), quindi il punteggio e' sempre
giustificabile davanti a chi lo legge.

Dove compare un termine conta quanto il termine stesso: in oggetto pesa piu'
che nel corpo, nel corpo piu' che nella parte citata di una risposta, e un
termine che compare solo dentro un indirizzo di posta
(``telemedicina@aslsalerno.it``) non dice nulla sul contenuto del messaggio.
"""

from __future__ import annotations

import math
import re
from typing import Iterable, List, Optional, Sequence, Tuple

from .config import ConfidenceSettings
from .matching import normalize
from .models import ConfidenceScore, Evidence

# --------------------------------------------------------------- espressioni

# Prestazioni erogate a distanza: il nucleo del tema "telemedicina".
TELEMEDICINE_TERMS = (
    (r"\btelemedicin\w*", "telemedicina"),
    (r"\btelevisit\w*", "televisita"),
    (r"\bteleconsult\w*", "teleconsulto"),
    (r"\btelemonitorag\w*|\btelemonitor\w*", "telemonitoraggio"),
    (r"\bteleassistenz\w*", "teleassistenza"),
    (r"\bterefertaz\w*|\bteleref\w*", "telerefertazione"),
    (r"\bvideovisit\w*|\bvisita a distanza\b|\bvisita da remoto\b", "visita a distanza"),
)

# Indizi di una prenotazione vera e propria.
BOOKING_TERMS = (
    (r"\bprenot\w*", "prenotazione", 2.4, 1.6),
    (r"\bappuntament\w*", "appuntamento", 1.6, 1.1),
    (r"\bimpegnativ\w*|\bricett\w*|\bprescrizion\w*", "impegnativa", 1.2, 1.2),
    (r"\bcodice prenotazione\b|\bnumero appuntamento\b|\bnumero ricetta\b",
     "riferimenti della prenotazione", 1.3, 1.3),
    (r"\bfissare\b|\bfissiamo\b|\bcalendarizzare\b", "fissare un appuntamento", 1.0, 0.9),
    (r"\bdisponibilit\w*|\bprimo posto utile\b|\bprima data utile\b",
     "richiesta di disponibilita", 0.7, 0.6),
    (r"\bvorrei\b|\bchiedo\b|\brichiedo\b|\bpotrei\b|\bnecessito\b",
     "richiesta esplicita", 0.4, 0.4),
    (r"\bpaziente\b|\bassistit\w*|\bcodice fiscale\b|\btessera sanitaria\b",
     "dati del paziente", 0.4, 0.4),
    (r"\b1501a\b", "codice 1501A", 1.2, 1.2),
)

# Contesti che escludono la prenotazione: il messaggio parla di telemedicina,
# ma per contarne gli accessi, fatturarla, venderla o segnalarne un guasto.
NOT_A_BOOKING = (
    (r"\baccessi\b|\bore di ferie\b|\bcartellin\w*|\bpresenz\w*",
     "rendiconto di accessi o presenze", -2.0),
    (r"\bvariazioni economiche\b|\bcompetenze\b|\bcedolin\w*|\bcompenso\b|\bcompensi\b",
     "pratica economica o stipendiale", -2.2),
    (r"\bfattur\w*|\bpreventiv\w*|\bofferta\b|\bofferte\b|\bproposta\b|\bpropost\w*|"
     r"\bcontratt\w*|\bsconto\b|\bcapitolat\w*|\bgara\b",
     "documento commerciale", -2.2),
    (r"\bnewsletter\b|\baudit news\b|\bunsubscribe\b|\bacademia\.edu\b|\bdownload del n\b",
     "comunicazione informativa o newsletter", -2.6),
    (r"\bsegnalazion\w*|\bmalfunzionament\w*|\bhelpdesk\b|\bhelp desk\b|\bticket\b|\banomali\w*",
     "segnalazione o assistenza tecnica", -1.4),
    (r"\bapertura agenda\b|\bagende\b|\boffering\b|\bconfigurat\w*|\bconfigurazione\b|"
     r"\battivazione agenda\b",
     "apertura o configurazione di agenda", -1.6),
    (r"\babilitazion\w*|\baccredit\w*|\bcredenzial\w*|\bpiattaforma\b|\bprofilazion\w*",
     "abilitazione a una piattaforma", -1.2),
    (r"\bcertificato di malattia\b|\bcertificato ecm\b|\bferie\b|\bpermesso\b",
     "documentazione del personale", -1.4),
    (r"\bdisdet\w*|\bdisdire\b|\bannull\w*|\bcancell\w*",
     "disdetta o annullamento", -2.4),
    (r"\bprogett\w*|\bbozza\b|\bmodulo i\b|\bfollow up\b",
     "documento progettuale", -1.2),
)

# Risposte automatiche e payload non risolti dal flusso: da scartare subito.
AUTOMATIC_REPLY = (
    (r"^\s*(accettata|accepted|rifiutata|declined|tentative|provvisoria)\s*:",
     "risposta automatica a un invito", -3.0),
    (r"\bunknown property\b|\bmessaggio generato automaticamente\b|\bno-reply\b|\bnoreply\b",
     "messaggio automatico o corpo non risolto", -2.2),
    (r"\bfuori sede\b|\bout of office\b|\bassenza dall'ufficio\b",
     "risposta di assenza", -2.5),
)

_EMAIL_ADDRESS = re.compile(r"[\w.+-]+@[\w.-]+\.\w+")
# Righe di instradamento di una risposta o di un inoltro: portano nomi di
# caselle, non l'argomento. "Da: Telemedicina <telemedicina@aslsalerno.it>" non
# rende il messaggio una questione di telemedicina. La riga "Oggetto:" invece
# si tiene: quella l'argomento ce l'ha davvero.
_ROUTING_LINE = re.compile(
    r"^\s*(da|from|a|to|cc|ccn|bcc|inviato|sent|mittente|destinatari)\s*:.*$",
    re.MULTILINE | re.IGNORECASE,
)
# Inizio della parte citata di una risposta o di un inoltro.
_QUOTED_MARKERS = (
    re.compile(r"^\s*da\s*:\s*.+", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^\s*from\s*:\s*.+", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^\s*-{6,}\s*$", re.MULTILINE),
    re.compile(r"^\s*_{6,}\s*$", re.MULTILINE),
)


class _Accumulator:
    """Somma i pesi degli indizi tenendo l'elenco di cio' che ha contato."""

    def __init__(self, bias: float) -> None:
        self._total = bias
        self.evidence: List[Evidence] = []

    def add(self, label: str, where: str, weight: float) -> None:
        if not weight:
            return
        self._total += weight
        self.evidence.append(Evidence(label=label, where=where, weight=round(weight, 2)))

    @property
    def total(self) -> float:
        return self._total


def score_telemedicine(
    subject: str,
    body: str,
    settings: ConfidenceSettings,
    *,
    attachment_names: Sequence[str] = (),
    document_text: str = "",
    document_matched: bool = False,
) -> ConfidenceScore:
    """Quanto e' sicuro che il messaggio riguardi la telemedicina.

    ``document_text`` e ``document_matched`` sono l'esito della lettura di
    allegati e foto: si passano solo dopo l'OCR, cosi' la stessa funzione serve
    sia per la stima iniziale (che decide se vale la pena chiamare l'OCR) sia
    per il punteggio definitivo.
    """
    zones = _Zones(subject, body)
    accumulator = _Accumulator(settings.telemedicine_bias)

    for pattern, label in TELEMEDICINE_TERMS:
        if zones.in_subject(pattern):
            accumulator.add(label, "oggetto", 3.2)
            if zones.in_visible_body(pattern):
                # Nell'oggetto e ripreso nel corpo: il tema e' quello, non un
                # riferimento di passaggio nel titolo.
                accumulator.add(f"{label} ripreso nel corpo", "corpo", 0.8)
        elif zones.in_visible_body(pattern):
            accumulator.add(label, "corpo", 2.0)
        elif zones.in_quoted_body(pattern):
            # In una risposta la parte citata e' contesto, non il messaggio.
            accumulator.add(f"{label} (testo citato)", "citato", 1.2)
        elif zones.in_addresses(pattern):
            # "telemedicina@aslsalerno.it" fra i destinatari non dice nulla sul
            # contenuto: e' l'ufficio che riceve, non l'argomento.
            accumulator.add(f"{label} (solo in indirizzi)", "indirizzi", 0.5)

    names = " ".join(attachment_names)
    if names:
        normalized_names = normalize(names)
        for pattern, label in TELEMEDICINE_TERMS:
            if re.search(pattern, normalized_names):
                accumulator.add(f"{label} nel nome del file", "allegati", 1.8)
                break

    if document_text:
        normalized_document = normalize(document_text)
        for pattern, label in TELEMEDICINE_TERMS:
            if re.search(pattern, normalized_document):
                accumulator.add(f"{label} nel documento letto", "documento", 2.4)
                break
    if document_matched:
        accumulator.add("documento con tutti i criteri", "documento", 2.5)

    for pattern, label, weight in AUTOMATIC_REPLY:
        if zones.in_subject(pattern) or zones.in_visible_body(pattern):
            accumulator.add(label, "oggetto" if zones.in_subject(pattern) else "corpo", weight)

    return _build(accumulator, settings, settings.telemedicine_threshold)


def score_booking(
    subject: str,
    body: str,
    settings: ConfidenceSettings,
    *,
    telemedicine: ConfidenceScore,
    document_matched: bool = False,
    document_text: str = "",
) -> ConfidenceScore:
    """Quanto e' sicuro che il messaggio sia una prenotazione di telemedicina.

    Il punteggio parte da quello di telemedicina: senza il tema non c'e'
    prenotazione di telemedicina, per quanti indizi di prenotazione ci siano.
    """
    zones = _Zones(subject, body)
    accumulator = _Accumulator(settings.booking_bias)

    # Il tema vale fino a due punti pieni, in proporzione alla sua sicurezza.
    accumulator.add(
        f"tema telemedicina al {telemedicine.percent:.0f}%",
        "telemedicina",
        round(2.0 * telemedicine.percent / 100.0, 2),
    )

    for pattern, label, subject_weight, body_weight in BOOKING_TERMS:
        if zones.in_subject(pattern):
            accumulator.add(label, "oggetto", subject_weight)
        elif zones.in_visible_body(pattern):
            accumulator.add(label, "corpo", body_weight)

    for pattern, label, weight in NOT_A_BOOKING:
        if zones.in_subject(pattern):
            accumulator.add(label, "oggetto", weight)
        elif zones.in_visible_body(pattern):
            # Nel corpo il contesto contrario pesa un po' meno che nell'oggetto.
            accumulator.add(label, "corpo", weight * 0.7)

    for pattern, label, weight in AUTOMATIC_REPLY:
        if zones.in_subject(pattern) or zones.in_visible_body(pattern):
            accumulator.add(label, "oggetto" if zones.in_subject(pattern) else "corpo", weight)

    if document_matched:
        # L'impegnativa allegata con tutti i criteri e' l'indizio piu' concreto.
        accumulator.add("documento con tutti i criteri", "documento", 2.8)
    elif document_text and re.search(r"\b1501a\b", normalize(document_text)):
        accumulator.add("codice 1501A nel documento letto", "documento", 1.2)

    return _build(accumulator, settings, settings.booking_threshold)


# ------------------------------------------------------------------ supporto


class _Zones:
    """Il testo diviso nelle zone che pesano in modo diverso."""

    def __init__(self, subject: str, body: str) -> None:
        self._subject = normalize(subject)
        # Si divide prima (i marcatori stanno proprio nelle righe di
        # instradamento), poi si ripulisce ciascuna parte.
        visible, quoted = _split_quoted(body)
        # Indirizzi e righe di instradamento escono dal testo: sono metadati di
        # consegna, non argomento del messaggio. Restano da parte, cosi' si puo'
        # comunque dire "il termine compare solo negli indirizzi".
        self._addresses = normalize(" ".join(_EMAIL_ADDRESS.findall(f"{subject} {body}")))
        self._visible = _readable(visible)
        self._quoted = _readable(quoted)

    def in_subject(self, pattern: str) -> bool:
        return bool(re.search(pattern, self._subject))

    def in_visible_body(self, pattern: str) -> bool:
        return bool(re.search(pattern, self._visible))

    def in_quoted_body(self, pattern: str) -> bool:
        return bool(re.search(pattern, self._quoted))

    def in_addresses(self, pattern: str) -> bool:
        return bool(re.search(pattern, self._addresses))


def _readable(text: str) -> str:
    """Solo il testo leggibile: via gli indirizzi e le righe di instradamento."""
    without_routing = _ROUTING_LINE.sub(" ", text)
    return normalize(_EMAIL_ADDRESS.sub(" ", without_routing))


def _split_quoted(body: str) -> Tuple[str, str]:
    """Separa cio' che ha scritto il mittente dalla parte citata o inoltrata."""
    if not body:
        return "", ""
    cut = min(
        (match.start() for match in _find_markers(body)),
        default=len(body),
    )
    return body[:cut], body[cut:]


def _find_markers(body: str) -> Iterable[re.Match]:
    for marker in _QUOTED_MARKERS:
        match = marker.search(body)
        if match is not None:
            yield match


def _build(
    accumulator: _Accumulator,
    settings: ConfidenceSettings,
    threshold: float,
) -> ConfidenceScore:
    percent = round(100.0 / (1.0 + math.exp(-accumulator.total)), 1)
    return ConfidenceScore(
        percent=percent,
        level=level_for(percent, settings),
        holds=percent >= threshold,
        evidence=accumulator.evidence,
    )


def level_for(percent: float, settings: Optional[ConfidenceSettings] = None) -> str:
    """Etichetta leggibile della percentuale, per chi non vuole leggere i numeri."""
    if percent >= 90:
        return "molto alta"
    if percent >= 70:
        return "alta"
    if percent >= 45:
        return "media"
    if percent >= 20:
        return "bassa"
    return "molto bassa"
