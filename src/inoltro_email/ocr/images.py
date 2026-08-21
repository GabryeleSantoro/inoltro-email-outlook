"""Riduzione delle immagini troppo grandi per ocr.space.

Il piano gratuito di ocr.space rifiuta i file oltre 1 MB. Una foto scattata
con il telefono - il modo piu' comune di mandare un'impegnativa - ne pesa
tranquillamente tre o quattro: prima veniva saltata, e con essa l'unico
documento utile del messaggio.

Ridurre un'immagine per l'OCR non e' come ridurla per guardarla. Conta la
leggibilita' dei caratteri, quindi:

* si scala il lato lungo per gradi, invece di comprimere e basta: e' la
  risoluzione a decidere se una lettera resta distinguibile, e scendere di
  qualita' JPEG sporca i bordi del testo proprio dove servono netti;
* si salva in JPEG con qualita' alta (85): il PNG di uno scatto fotografico
  resta grande perche' non ha aree uniformi da comprimere;
* ci si ferma al primo passo che sta sotto il limite, senza rimpicciolire piu'
  del necessario.

Se anche il passo piu' piccolo resta sopra il limite si restituisce comunque
l'ultimo risultato: un tentativo di lettura vale piu' di un allegato saltato.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# Lato lungo, in pixel, dei tentativi successivi. Sotto i 1000 pixel il testo
# di un'impegnativa fotografata diventa illeggibile anche per un umano, quindi
# la scala non scende oltre.
SCALE_PROGRESSIVE = (2400, 2000, 1600, 1300, 1000)
QUALITA_JPEG = 85


class ImageError(Exception):
    """L'immagine non e' leggibile o non si riesce a ridurla."""


def riduci_sotto(
    path: Path,
    limite_byte: int,
    destinazione: Path,
) -> Tuple[Path, str]:
    """Riduce l'immagine finche' non sta sotto ``limite_byte``.

    Restituisce ``(percorso, descrizione)``. Il percorso e' quello originale se
    l'immagine era gia' abbastanza piccola; la descrizione racconta cosa e'
    stato fatto e finisce nei log e nella risposta.
    """
    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - dipendenza dichiarata
        raise ImageError(
            "Pillow non installato: impossibile ridurre le immagini troppo grandi."
        ) from exc

    dimensione_iniziale = path.stat().st_size
    if dimensione_iniziale <= limite_byte:
        return path, ""

    try:
        with Image.open(path) as immagine:
            immagine.load()
            originale = _in_rgb(immagine)
            larghezza, altezza = originale.size
    except Exception as exc:  # noqa: BLE001 - immagine corrotta o formato ignoto
        raise ImageError(f"immagine non leggibile ({exc})") from exc

    lato_lungo = max(larghezza, altezza)
    ultimo: Optional[Path] = None
    ultima_dimensione = dimensione_iniziale

    for lato in _passi(lato_lungo):
        ridotta = _salva_scalata(originale, lato, destinazione)
        ultima_dimensione = ridotta.stat().st_size
        ultimo = ridotta
        if ultima_dimensione <= limite_byte:
            descrizione = (
                f"immagine ridotta da {larghezza}x{altezza} ({dimensione_iniziale} byte) "
                f"a lato lungo {lato} ({ultima_dimensione} byte) per il limite dell'OCR"
            )
            logger.info("%s: %s", path.name, descrizione)
            return ridotta, descrizione

    if ultimo is None:
        raise ImageError("nessuna riduzione possibile per questa immagine")

    # Anche il passo piu' piccolo sfora: si prova lo stesso, l'API potrebbe
    # accettarlo (i limiti dei piani a pagamento sono piu' alti) e comunque un
    # tentativo vale piu' di un allegato non letto.
    descrizione = (
        f"immagine ridotta al minimo ({ultima_dimensione} byte) ma ancora sopra "
        f"il limite di {limite_byte} byte: inviata comunque"
    )
    logger.warning("%s: %s", path.name, descrizione)
    return ultimo, descrizione


def _passi(lato_lungo: int) -> List[int]:
    """Dimensioni da provare, dalla piu' grande utile alla piu' piccola."""
    passi = [lato for lato in SCALE_PROGRESSIVE if lato < lato_lungo]
    if not passi:
        # Immagine gia' piccola di lato ma pesante come file (PNG senza
        # compressione, scansione a colori): si tiene la dimensione e si
        # guadagna tutto dalla conversione in JPEG. Ingrandirla la farebbe solo
        # pesare di piu' senza aggiungere un solo dettaglio leggibile.
        passi = [lato_lungo]
    return passi


def _salva_scalata(immagine, lato_lungo: int, destinazione: Path) -> Path:
    from PIL import Image

    larghezza, altezza = immagine.size
    fattore = lato_lungo / max(larghezza, altezza)
    nuova = (max(1, round(larghezza * fattore)), max(1, round(altezza * fattore)))

    # LANCZOS e' il filtro che conserva meglio i bordi netti del testo.
    ridotta = immagine.resize(nuova, Image.LANCZOS)
    percorso = destinazione.with_name(f"{destinazione.stem}_{lato_lungo}.jpg")
    ridotta.save(percorso, format="JPEG", quality=QUALITA_JPEG, optimize=True)
    return percorso


def _in_rgb(immagine):
    """Porta l'immagine in RGB: il JPEG non ha canale di trasparenza.

    Le scansioni arrivano spesso come PNG con trasparenza o in scala di grigi
    a un bit; appiattirle su bianco e' cio' che fa anche uno scanner.
    """
    from PIL import Image

    if immagine.mode in ("RGB", "L"):
        return immagine
    if immagine.mode in ("RGBA", "LA", "P"):
        convertita = immagine.convert("RGBA")
        sfondo = Image.new("RGBA", convertita.size, (255, 255, 255, 255))
        return Image.alpha_composite(sfondo, convertita).convert("RGB")
    return immagine.convert("RGB")
