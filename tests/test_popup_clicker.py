from __future__ import annotations

from inoltro_email import popup_clicker


class FintoPulsante:
    def __init__(self, chiude_dopo_click: bool) -> None:
        self.visibile = True
        self.chiude_dopo_click = chiude_dopo_click
        self.click_chiamati = 0

    def invoke(self) -> None:
        raise RuntimeError("UI Automation non disponibile")

    def click_input(self) -> None:
        self.click_chiamati += 1
        if self.chiude_dopo_click:
            self.visibile = False

    def exists(self, timeout: float = 0) -> bool:
        return self.visibile

    def is_visible(self) -> bool:
        return self.visibile


def test_click_input_e_successo_solo_se_conferma_si_chiude(monkeypatch) -> None:
    monkeypatch.setattr(popup_clicker.time, "sleep", lambda _secondi: None)
    pulsante = FintoPulsante(chiude_dopo_click=True)

    assert popup_clicker._try_invoke(pulsante) is True
    assert pulsante.click_chiamati == 1


def test_click_input_non_e_successo_se_conferma_resta_visibile(monkeypatch) -> None:
    monkeypatch.setattr(popup_clicker.time, "sleep", lambda _secondi: None)
    pulsante = FintoPulsante(chiude_dopo_click=False)

    assert popup_clicker._try_invoke(pulsante) is False
    assert pulsante.click_chiamati == 1


def test_modulo_non_blocca_input_di_windows() -> None:
    assert not hasattr(popup_clicker, "BlockInput")
