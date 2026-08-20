"""Riconoscimento dei termini scritti male.

Le parole che contano per questo servizio si sbagliano spesso, in due modi:

* **a mano**, da chi scrive di fretta - "telvisita", "prenotazine",
  "impegnatva", "telemdicina";
* **dall'OCR**, che su una scansione storta legge "teIevisita" o "visifa".

Le espressioni regolari di ``confidence.py`` restano il riconoscimento
principale, perche' con la radice della parola coprono tutte le forme flesse
("prenotare", "prenotazioni", "prenotato") senza rischio di equivoci. Questo
modulo interviene solo *dopo*, quando la regola non ha trovato nulla: confronta
ogni parola del testo con le forme corrette e accetta le differenze piccole.

La distanza usata e' quella di Damerau-Levenshtein, che conta anche lo scambio
di due lettere vicine ("telveisita"): e' l'errore di battitura piu' comune e
una distanza di Levenshtein semplice lo conterebbe come due modifiche.

Quanta differenza si accetta dipende dalla lunghezza della parola: su
"telemonitoraggio" due lettere sbagliate restano riconoscibili, su "visita" no
- a distanza uno diventerebbe "vista", che e' un'altra parola. Le collisioni
note stanno in ``PAROLE_ESCLUSE``.
"""

from __future__ import annotations

import re
from typing import Dict, Iterable, Mapping, Optional, Set

from .matching import normalize

# Forma corretta -> termine di riferimento. Le forme flesse piu' comuni sono
# elencate perche' fanno da bersaglio al confronto: "prenotazine" somiglia a
# "prenotazione" ma non a "prenotare".
FORME_CORRETTE: Dict[str, str] = {
    "televisita": "televisita", "televisite": "televisita",
    "telemedicina": "telemedicina", "telemedicine": "telemedicina",
    "teleconsulto": "teleconsulto", "teleconsulti": "teleconsulto",
    "telemonitoraggio": "telemonitoraggio",
    "teleassistenza": "teleassistenza",
    "videovisita": "videovisita", "videovisite": "videovisita",
    "prenotazione": "prenotazione", "prenotazioni": "prenotazione",
    "prenotare": "prenotazione", "prenotata": "prenotazione",
    "prenotato": "prenotazione", "prenotarsi": "prenotazione",
    "appuntamento": "appuntamento", "appuntamenti": "appuntamento",
    "impegnativa": "impegnativa", "impegnative": "impegnativa",
    "prescrizione": "prescrizione", "prescrizioni": "prescrizione",
    "terapeutico": "terapeutico", "terapeutici": "terapeutico",
    "terapeutica": "terapeutico", "terapeutiche": "terapeutico",
    "visita": "visita", "visite": "visita",
    "ricetta": "ricetta", "ricette": "ricetta",
}

# Parole italiane che cadrebbero dentro la tolleranza ma non c'entrano nulla.
# "vista" dista una sola lettera da "visita": senza questo elenco "punto di
# vista" varrebbe come una richiesta di visita.
PAROLE_ESCLUSE: Set[str] = {
    "vista", "viste", "visto", "visti", "avvisi", "avviso", "rivista", "riviste",
    "ricerca", "ricerche", "ricevuta", "ricevute", "vicenda",
    "terapeutas", "telefonica", "telefoniche",
}

_PAROLA = re.compile(r"[a-z]+")

# Sotto le sei lettere non si tollera nulla: la differenza di una lettera su
# una parola corta cambia il significato piu' spesso di quanto corregga.
_LUNGHEZZA_MINIMA = 6
_SOGLIA_DISTANZA_DUE = 11


def distanza_massima(parola: str) -> int:
    """Quante differenze si accettano su una parola di questa lunghezza."""
    if len(parola) >= _SOGLIA_DISTANZA_DUE:
        return 2
    if len(parola) >= _LUNGHEZZA_MINIMA:
        return 1
    return 0


def trova_termini(
    text: str,
    forme: Optional[Mapping[str, str]] = None,
) -> Dict[str, str]:
    """Termini riconosciuti nel testo, anche se scritti male.

    Restituisce ``{termine: forma trovata}``. La forma trovata coincide con il
    termine quando la parola era scritta bene: chi legge la risposta puo' cosi'
    vedere che cosa e' stato interpretato e come.
    """
    forme = FORME_CORRETTE if forme is None else forme
    trovati: Dict[str, str] = {}

    for parola in _parole(text):
        termine = forme.get(parola)
        if termine is not None:
            trovati[termine] = parola  # scritta bene: nessun dubbio
            continue
        if parola in PAROLE_ESCLUSE:
            continue

        vicino = _piu_vicina(parola, forme)
        if vicino is not None and vicino not in trovati:
            trovati[vicino] = parola
    return trovati


def _parole(text: str) -> Iterable[str]:
    if not text:
        return ()
    return _PAROLA.findall(normalize(text))


def _piu_vicina(parola: str, forme: Mapping[str, str]) -> Optional[str]:
    """Termine piu' somigliante alla parola, se rientra nella tolleranza."""
    migliore: Optional[str] = None
    distanza_migliore = 99

    for forma, termine in forme.items():
        limite = distanza_massima(forma)
        if limite == 0 or abs(len(forma) - len(parola)) > limite:
            continue
        distanza = distanza_entro(parola, forma, limite)
        if distanza is not None and distanza < distanza_migliore:
            migliore, distanza_migliore = termine, distanza
            if distanza == 1:
                break  # piu' vicino di cosi' non serve cercare
    return migliore


def distanza_entro(prima: str, seconda: str, limite: int) -> Optional[int]:
    """Distanza di Damerau-Levenshtein, o None se supera ``limite``.

    Il calcolo si ferma appena tutta la riga corrente sfora il limite: sui
    confronti che non possono riuscire - la maggior parte - non si arriva
    nemmeno a meta' tabella.
    """
    if prima == seconda:
        return 0
    if abs(len(prima) - len(seconda)) > limite:
        return None

    precedente_precedente: list = []
    precedente = list(range(len(seconda) + 1))

    for indice_prima, lettera_prima in enumerate(prima, start=1):
        corrente = [indice_prima] + [0] * len(seconda)
        for indice_seconda, lettera_seconda in enumerate(seconda, start=1):
            costo = 0 if lettera_prima == lettera_seconda else 1
            corrente[indice_seconda] = min(
                corrente[indice_seconda - 1] + 1,          # inserimento
                precedente[indice_seconda] + 1,            # cancellazione
                precedente[indice_seconda - 1] + costo,    # sostituzione
            )
            # Scambio di due lettere vicine: "telveisita" -> "televisita".
            if (
                indice_prima > 1
                and indice_seconda > 1
                and lettera_prima == seconda[indice_seconda - 2]
                and prima[indice_prima - 2] == lettera_seconda
            ):
                corrente[indice_seconda] = min(
                    corrente[indice_seconda],
                    precedente_precedente[indice_seconda - 2] + 1,
                )
        if min(corrente) > limite:
            return None
        precedente_precedente, precedente = precedente, corrente

    distanza = precedente[-1]
    return distanza if distanza <= limite else None
