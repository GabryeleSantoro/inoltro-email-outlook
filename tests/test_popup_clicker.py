from __future__ import annotations

import contextlib
import sys
from types import SimpleNamespace

from inoltro_email import popup_clicker


class FintoPulsante:
    def __init__(self, chiude_dopo_click: bool, invoke_disponibile: bool = False) -> None:
        self.visibile = True
        self.chiude_dopo_click = chiude_dopo_click
        self.invoke_disponibile = invoke_disponibile
        self.invoke_chiamati = 0
        self.click_chiamati = 0

    def invoke(self) -> None:
        self.invoke_chiamati += 1
        if not self.invoke_disponibile:
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


def test_verifica_esterna_evita_loop_con_wrapper_uia_obsoleto(monkeypatch) -> None:
    monkeypatch.setattr(popup_clicker.time, "sleep", lambda _secondi: None)
    pulsante = FintoPulsante(
        chiude_dopo_click=False,
        invoke_disponibile=True,
    )

    assert popup_clicker._try_invoke(
        pulsante,
        confirmation_closed=lambda: True,
    ) is True
    assert pulsante.invoke_chiamati == 1
    assert pulsante.click_chiamati == 0
    assert pulsante.visibile is True  # wrapper vecchio rimasto in cache


def test_popup_visto_e_poi_sparito_termina_la_ricerca(monkeypatch) -> None:
    class FintaFinestra:
        handle = 123

        def is_visible(self) -> bool:
            return True

        def window_text(self) -> str:
            return "Power Automate"

    class FintoDesktop:
        def __init__(self, backend: str) -> None:
            self.backend = backend

        def windows(self, **_kwargs):
            return [FintaFinestra()]

    monkeypatch.setitem(
        sys.modules,
        "pywinauto",
        SimpleNamespace(Desktop=FintoDesktop),
    )
    monkeypatch.setattr(popup_clicker, "_dump_all_visible_windows", lambda _backend: [])
    monkeypatch.setattr(popup_clicker, "_dump_window_tree", lambda _window: [])
    monkeypatch.setattr(popup_clicker, "SetForegroundWindow", lambda _handle: True)
    monkeypatch.setattr(
        popup_clicker,
        "_focus_lock",
        lambda _window, timeout: contextlib.nullcontext(),
    )
    monkeypatch.setattr(popup_clicker, "_click_button_uia", lambda *_args: False)
    monkeypatch.setattr(popup_clicker, "_click_button_win32", lambda *_args: False)
    monkeypatch.setattr(popup_clicker, "_window_has_uia_confirmation", lambda _window: True)
    monkeypatch.setattr(popup_clicker, "_uia_confirmation_present", lambda _title: False)

    assert popup_clicker.click_continue(timeout=1) is True


def test_modulo_non_blocca_input_di_windows() -> None:
    assert not hasattr(popup_clicker, "BlockInput")
