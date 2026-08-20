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
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from .config import ConfidenceSettings
from .matching import normalize
from .models import ConfidenceScore, Evidence
from .spelling import trova_termini

# --------------------------------------------------------------- espressioni

# Prestazioni erogate a distanza: il nucleo del tema "telemedicina".
# Il terzo elemento elenca i termini che ``spelling`` sa riconoscere anche
# scritti male: si usano solo quando l'espressione regolare non trova nulla.
TELEMEDICINE_TERMS = (
    (r"\btelemedicin\w*", "telemedicina", ("telemedicina",)),
    (r"\btelevisit\w*", "televisita", ("televisita",)),
    (r"\bteleconsult\w*", "teleconsulto", ("teleconsulto",)),
    (r"\btelemonitorag\w*|\btelemonitor\w*", "telemonitoraggio", ("telemonitoraggio",)),
    (r"\bteleassistenz\w*", "teleassistenza", ("teleassistenza",)),
    (r"\bterefertaz\w*|\bteleref\w*", "telerefertazione", ()),
    (r"\bvideovisit\w*|\bvisita a distanza\b|\bvisita da remoto\b",
     "visita a distanza", ("videovisita",)),
)

# Indizi di una prenotazione vera e propria: (regola, etichetta, peso
# nell'oggetto, peso nel corpo, termini riconosciuti anche se scritti male).
#
# "televisita" e "telemedicina" compaiono anche qui, oltre che fra i termini
# del tema: nominare la prestazione mentre si chiede un appuntamento e' un
# indizio in piu'. I pesi sono pero' bassi apposta, perche' il tema entra gia'
# nel punteggio per conto suo e non deve contare due volte per intero.
BOOKING_TERMS = (
    (r"\bprenot\w*", "prenotazione", 2.4, 1.6, ("prenotazione",)),
    (r"\bappuntament\w*", "appuntamento", 1.6, 1.1, ("appuntamento",)),
    (r"\bimpegnativ\w*|\bricett\w*|\bprescrizion\w*", "impegnativa", 1.3, 1.2,
     ("impegnativa", "ricetta", "prescrizione")),
    (r"\bpian\w+ terapeutic\w+", "piano terapeutico", 1.0, 0.8, ("terapeutico",)),
    (r"\bvisit\w*", "visita", 1.2, 0.7, ("visita",)),
    (r"\btelevisit\w*", "televisita", 1.6, 0.9, ("televisita",)),
    (r"\btelemedicin\w*", "telemedicina", 1.2, 0.7, ("telemedicina",)),
    (r"\bcodice prenotazione\b|\bnumero appuntamento\b|\bnumero ricetta\b",
     "riferimenti della prenotazione", 1.3, 1.3, ()),
    (r"\bfissare\b|\bfissiamo\b|\bcalendarizzare\b", "fissare un appuntamento", 1.0, 0.9, ()),
    (r"\bdisponibilit\w*|\bprimo posto utile\b|\bprima data utile\b",
     "richiesta di disponibilita", 0.7, 0.6, ()),
    (r"\bvorrei\b|\bchiedo\b|\brichiedo\b|\brichiest\w*|\bpotrei\b|\bnecessito\b",
     "richiesta esplicita", 0.4, 0.4, ()),
    (r"\bpaziente\b|\bassistit\w*|\bcodice fiscale\b|\btessera sanitaria\b",
     "dati del paziente", 0.4, 0.4, ()),
    (r"\b1501a\b", "codice 1501A", 1.2, 1.2, ()),
)

# Peso di un termine del tema secondo il punto del messaggio in cui compare.
# Il peso del corpo deve bastare da solo a superare la soglia: un messaggio che
# scrive "vorrei prenotare una televisita" riguarda la telemedicina anche se
# l'oggetto dice solo "Richiesta". Il rumore da tenere fuori sta nelle altre due
# zone - il testo citato di una risposta e i nomi delle caselle in copia - e
# quelle restano volutamente leggere.
PESI_PER_ZONA = {"oggetto": 3.2, "corpo": 2.6, "citato": 1.2, "indirizzi": 0.5}

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
    (r"\bprogett\w*|\bbozza\b|\bmodulo i\b|\bfollow up\b",
     "documento progettuale", -1.2),
)

# Chi scrive per disdire non sta prenotando, e lo fa usando le stesse parole di
# una prenotazione ("vorrei disdire l'appuntamento di televisita prenotato"):
# il peso deve poter annullare tutti gli indizi a favore messi insieme. Per lo
# stesso motivo vale pieno anche nel corpo, a differenza degli altri contesti:
# "vorrei disdire" scritto nel corpo e' chiaro quanto nell'oggetto.
CANCEL_SIGNALS = (
    (r"\bdisdet\w*|\bdisdire\b|\bannull\w*|\bcancell\w*",
     "disdetta o annullamento", -4.0),
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

    for pattern, label, fuzzy_terms in TELEMEDICINE_TERMS:
        zona, scorretta = zones.find(pattern, fuzzy_terms)
        if zona is None:
            continue
        accumulator.add(_etichetta(label, zona, scorretta), zona, PESI_PER_ZONA[zona])
        if zona == "oggetto" and zones.find(pattern, fuzzy_terms, ("corpo",))[0]:
            # Nell'oggetto e ripreso nel corpo: il tema e' quello, non un
            # riferimento di passaggio nel titolo.
            accumulator.add(f"{label} ripreso nel corpo", "corpo", 0.8)

    nome_trovato, nome_scorretto = _cerca_nel_testo(" ".join(attachment_names))
    if nome_trovato is not None:
        accumulator.add(
            _etichetta(f"{nome_trovato} nel nome del file", "allegati", nome_scorretto),
            "allegati", 1.8,
        )

    documento_trovato, documento_scorretto = _cerca_nel_testo(document_text)
    if documento_trovato is not None:
        # L'OCR sbaglia proprio queste parole: la tolleranza serve soprattutto qui.
        accumulator.add(
            _etichetta(f"{documento_trovato} nel documento letto", "documento", documento_scorretto),
            "documento", 2.4,
        )
    if document_matched:
        accumulator.add("documento con tutti i criteri", "documento", 2.5)

    _apply_context(accumulator, zones, AUTOMATIC_REPLY)

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

    for pattern, label, subject_weight, body_weight, fuzzy_terms in BOOKING_TERMS:
        zona, scorretta = zones.find(pattern, fuzzy_terms, ("oggetto", "corpo"))
        if zona is None:
            continue
        peso = subject_weight if zona == "oggetto" else body_weight
        accumulator.add(_etichetta(label, zona, scorretta), zona, peso)

    # Nel corpo il contesto contrario pesa un po' meno che nell'oggetto.
    _apply_context(accumulator, zones, NOT_A_BOOKING, body_factor=0.7)
    _apply_context(accumulator, zones, CANCEL_SIGNALS)
    _apply_context(accumulator, zones, AUTOMATIC_REPLY)

    if document_matched:
        # L'impegnativa allegata con tutti i criteri e' l'indizio piu' concreto.
        accumulator.add("documento con tutti i criteri", "documento", 2.8)
    elif document_text and re.search(r"\b1501a\b", normalize(document_text)):
        accumulator.add("codice 1501A nel documento letto", "documento", 1.2)

    return _build(accumulator, settings, settings.booking_threshold)


# ------------------------------------------------------------------ supporto


def _apply_context(
    accumulator: "_Accumulator",
    zones: "_Zones",
    signals: Sequence[Tuple[str, str, float]],
    *,
    body_factor: float = 1.0,
) -> None:
    """Applica gli indizi di contesto, che valgono solo scritti per esteso.

    Non passano dal riconoscimento degli errori: sono espressioni di contorno
    ("variazioni economiche", "apertura agenda"), non termini clinici, e una
    somiglianza approssimata porterebbe piu' equivoci che aiuto.
    """
    for pattern, label, weight in signals:
        zona, _ = zones.find(pattern, (), ("oggetto", "corpo"))
        if zona is None:
            continue
        accumulator.add(label, zona, weight if zona == "oggetto" else weight * body_factor)


def _cerca_nel_testo(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Primo termine di telemedicina in un testo senza zone (nomi, documenti)."""
    if not text:
        return None, None
    trovati = trova_termini(text)
    for _pattern, label, fuzzy_terms in TELEMEDICINE_TERMS:
        for termine in fuzzy_terms:
            forma = trovati.get(termine)
            if forma is not None:
                return label, (forma if forma != termine else None)
    return None, None


def _etichetta(label: str, zona: str, scorretta: Optional[str]) -> str:
    """Etichetta dell'indizio, con la forma davvero letta se era scorretta."""
    if scorretta is not None:
        label = f"{label} (scritto '{scorretta}')"
    if zona == "citato":
        return f"{label} (testo citato)"
    if zona == "indirizzi":
        # "telemedicina@aslsalerno.it" fra i destinatari non dice nulla sul
        # contenuto: e' l'ufficio che riceve, non l'argomento.
        return f"{label} (solo in indirizzi)"
    return label


class _Zones:
    """Il testo diviso nelle zone che pesano in modo diverso.

    Ogni zona viene cercata due volte: con l'espressione regolare, che copre le
    forme flesse, e - solo se quella non trova nulla - con il riconoscimento
    delle parole scritte male.
    """

    ORDINE = ("oggetto", "corpo", "citato", "indirizzi")

    def __init__(self, subject: str, body: str) -> None:
        # Si divide prima (i marcatori stanno proprio nelle righe di
        # instradamento), poi si ripulisce ciascuna parte.
        visible, quoted = _split_quoted(body)
        # Indirizzi e righe di instradamento escono dal testo: sono metadati di
        # consegna, non argomento del messaggio. Restano da parte, cosi' si puo'
        # comunque dire "il termine compare solo negli indirizzi".
        self._testo = {
            "oggetto": normalize(subject),
            "corpo": _readable(visible),
            "citato": _readable(quoted),
            "indirizzi": normalize(" ".join(_EMAIL_ADDRESS.findall(f"{subject} {body}"))),
        }
        # Le parole scritte male si cercano una volta per zona, non una volta
        # per regola: il confronto costa, i termini da cercare sono sempre gli
        # stessi.
        self._scorrette: Dict[str, Dict[str, str]] = {
            zona: trova_termini(testo) for zona, testo in self._testo.items()
        }

    def find(
        self,
        pattern: str,
        fuzzy_terms: Sequence[str] = (),
        zones: Sequence[str] = ORDINE,
    ) -> Tuple[Optional[str], Optional[str]]:
        """Prima zona in cui compare il termine.

        Restituisce ``(zona, forma scorretta)``: la forma scorretta e' valorizzata
        solo quando il termine e' stato riconosciuto nonostante un errore di
        scrittura, e finisce nella risposta perche' si veda cosa e' stato letto.
        """
        for zona in zones:
            if re.search(pattern, self._testo[zona]):
                return zona, None
            scorretta = self._forma_scorretta(zona, fuzzy_terms)
            if scorretta is not None:
                return zona, scorretta
        return None, None

    def _forma_scorretta(self, zona: str, fuzzy_terms: Sequence[str]) -> Optional[str]:
        trovate = self._scorrette[zona]
        for termine in fuzzy_terms:
            forma = trovate.get(termine)
            # Se la parola era scritta bene l'ha gia' presa l'espressione
            # regolare: qui interessa solo cio' che quella non ha visto.
            if forma is not None and forma != termine:
                return forma
        return None


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
