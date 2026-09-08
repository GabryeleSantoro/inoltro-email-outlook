"""Avvio rapido del servizio: ``python main.py``.

Equivalente a ``python -m inoltro_email serve``; gli argomenti aggiuntivi, per
esempio ``--dev``, vengono inoltrati al comando ``serve``. Utile dove si
preferisce un singolo file di ingresso (per esempio in alcuni servizi di hosting).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from inoltro_email.__main__ import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main(["serve", *sys.argv[1:]]))
