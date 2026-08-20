"""Test della riduzione delle immagini troppo grandi per ocr.space."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from conftest import make_photo
from PIL import Image

from inoltro_email.ocr.images import ImageError, riduci_sotto

LIMITE = 1_048_576  # il limite del piano gratuito


@pytest.fixture
def foto(tmp_path: Path) -> Path:
    percorso = tmp_path / "impegnativa.png"
    percorso.write_bytes(make_photo())
    return percorso


def test_immagine_gia_piccola_non_viene_toccata(tmp_path: Path) -> None:
    piccola = tmp_path / "piccola.png"
    Image.new("RGB", (200, 200), "white").save(piccola)

    percorso, nota = riduci_sotto(piccola, LIMITE, tmp_path / "lavoro")

    assert percorso == piccola
    assert nota == ""


def test_foto_ridotta_sotto_il_limite(foto: Path, tmp_path: Path) -> None:
    assert foto.stat().st_size > LIMITE

    percorso, nota = riduci_sotto(foto, LIMITE, tmp_path / "lavoro")

    assert percorso != foto
    assert percorso.stat().st_size <= LIMITE
    assert "ridotta" in nota


def test_si_conserva_la_risoluzione_piu_alta_possibile(foto: Path, tmp_path: Path) -> None:
    """Per l'OCR conta la leggibilita': non si rimpicciolisce piu' del necessario."""
    percorso, _ = riduci_sotto(foto, LIMITE, tmp_path / "lavoro")

    with Image.open(percorso) as ridotta:
        lato_lungo = max(ridotta.size)
    with Image.open(foto) as originale:
        lato_originale = max(originale.size)

    assert lato_lungo < lato_originale
    assert lato_lungo >= 2000  # il primo scalino che basta, non il piu' piccolo


def test_le_proporzioni_restano_invariate(foto: Path, tmp_path: Path) -> None:
    percorso, _ = riduci_sotto(foto, LIMITE, tmp_path / "lavoro")

    with Image.open(foto) as originale:
        atteso = originale.size[0] / originale.size[1]
    with Image.open(percorso) as ridotta:
        ottenuto = ridotta.size[0] / ridotta.size[1]

    assert abs(atteso - ottenuto) < 0.01


def test_immagine_piccola_di_lato_ma_pesante_non_viene_ingrandita(tmp_path: Path) -> None:
    """Si guadagna dalla conversione in JPEG, non da un ingrandimento inutile."""
    percorso = tmp_path / "scansione.png"
    percorso.write_bytes(make_photo(700, 500))

    ridotta, _nota = riduci_sotto(percorso, 20_000, tmp_path / "lavoro")

    with Image.open(ridotta) as immagine:
        assert max(immagine.size) <= 700


def test_trasparenza_appiattita_su_bianco(tmp_path: Path) -> None:
    """Il JPEG non ha canale alfa: le scansioni in PNG arrivano spesso cosi'."""
    percorso = tmp_path / "trasparente.png"
    Image.new("RGBA", (2400, 1800), (0, 0, 0, 0)).save(percorso)

    ridotta, _nota = riduci_sotto(percorso, 1_000, tmp_path / "lavoro")

    with Image.open(ridotta) as immagine:
        assert immagine.mode == "RGB"
        assert immagine.getpixel((0, 0)) == (255, 255, 255)


def test_immagine_illeggibile_solleva(tmp_path: Path) -> None:
    percorso = tmp_path / "rotta.png"
    percorso.write_bytes(b"non sono un'immagine")

    with pytest.raises(ImageError):
        riduci_sotto(percorso, 10, tmp_path / "lavoro")


def test_si_invia_comunque_se_il_minimo_non_basta(foto: Path, tmp_path: Path) -> None:
    """Un tentativo di lettura vale piu' di un allegato saltato."""
    percorso, nota = riduci_sotto(foto, 1_000, tmp_path / "lavoro")

    assert percorso.is_file()
    assert "ancora sopra il limite" in nota
