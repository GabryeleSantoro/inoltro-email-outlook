"""Click automatico sul popup 'Continue' di Power Automate Desktop.

Quando un flow viene avviato da .lnk, PAD mostra una finestra che chiede
conferma prima di eseguire. Questo modulo:

1. Cerca la finestra di conferma (titolo configurabile).
2. Disabilita l'input utente per il minimo tempo necessario (``BlockInput``)
   cosi' nessun'altra finestra puo' rubare il focus.
3. Porta la finestra in primo piano e la rende TOPMOST.
   4. Clicca il pulsante "Continua" (o testo configurabile).
5. Ripristina input e stato della finestra.

Uso tipico::

    from inoltro_email.popup_clicker import click_continue

    click_continue()                         # defaults
    click_continue(title="My Flow", timeout=15)  # custom
"""

from __future__ import annotations

import contextlib
import ctypes
import logging
import time
from ctypes import wintypes
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Windows API via ctypes (zero external deps per il locking)
# ---------------------------------------------------------------------------

user32 = ctypes.windll.user32  # type: ignore[attr-defined]

BlockInput = user32.BlockInput
BlockInput.argtypes = [wintypes.BOOL]
BlockInput.restype = wintypes.BOOL

SetWindowPos = user32.SetWindowPos
SetWindowPos.argtypes = [
    wintypes.HWND, wintypes.HWND,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT,
]
SetWindowPos.restype = wintypes.BOOL

GetForegroundWindow = user32.GetForegroundWindow
GetForegroundWindow.restype = wintypes.HWND

SetForegroundWindow = user32.SetForegroundWindow
SetForegroundWindow.argtypes = [wintypes.HWND]
SetForegroundWindow.restype = wintypes.BOOL

HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_SHOWWINDOW = 0x0040

# ---------------------------------------------------------------------------
# Default parametri
# ---------------------------------------------------------------------------

DEFAULT_POPUP_TITLE = "Power Automate"
DEFAULT_BUTTON_TEXT = "Continua"
DEFAULT_POPUP_TIMEOUT = 10
DEFAULT_POLL_INTERVAL = 0.3


# ---------------------------------------------------------------------------
# Focus lock
# ---------------------------------------------------------------------------

@contextlib.contextmanager
def _focus_lock(window, timeout: float = 2.0):
    """Disabilita input + finestra topmost per ``timeout`` secondi.

    Viene usato ``BlockInput`` (richiede process con privileges) per impedire
    all'utente di cliccare altrove durante l'operazione.  La finestra viene
    resa TOPMOST per evitare che qualcosa la copra.

    Il blocco e' limitato a ``timeout`` secondi per sicurezza: se qualcosa
    va storto e il click non parte, l'utente riprende il controllo.
    """
    try:
        BlockInput(True)
        SetWindowPos(
            window.handle, HWND_TOPMOST,
            0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW,
        )
        logger.debug("Focus lock attivato (timeout=%.1fs).", timeout)
        yield
    except Exception:
        logger.exception("Errore durante focus lock.")
        raise
    finally:
        BlockInput(False)
        SetWindowPos(
            window.handle, HWND_NOTOPMOST,
            0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW,
        )
        logger.debug("Focus lock rilasciato.")


# ---------------------------------------------------------------------------
# Ricerca popup
# ---------------------------------------------------------------------------

def _try_uia(title_re: str, timeout: float, poll: float):
    """Cerca con pywinauto UIA backend (consigliato per app UWP/WPF)."""
    from pywinauto import Desktop

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            desktop = Desktop(backend="uia")
            windows = desktop.windows(title_re=title_re)
            for w in windows:
                if w.is_visible():
                    return w
        except Exception:
            pass
        time.sleep(poll)
    return None


def _try_win32(title_re: str, timeout: float, poll: float):
    """Fallback con pywinauto Win32 backend (app Win32 classiche)."""
    from pywinauto import Desktop

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            desktop = Desktop(backend="win32")
            windows = desktop.windows(title_re=title_re)
            for w in windows:
                if w.is_visible():
                    return w
        except Exception:
            pass
        time.sleep(poll)
    return None


def find_popup(
    title: str = DEFAULT_POPUP_TITLE,
    timeout: float = DEFAULT_POPUP_TIMEOUT,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
):
    """Cerca la finestra di conferma PAD.

    Prova UIA prima, poi Win32 come fallback.  Restituisce un wrapper
    pywinauto oppure ``None`` se non trovata entro ``timeout`` secondi.
    """
    import re
    title_re = re.compile(re.escape(title), re.IGNORECASE)

    logger.info(
        "Ricerca popup '%s' (timeout=%.0fs)...", title, timeout,
    )

    popup = _try_uia(title_re, timeout, poll_interval)
    if popup is not None:
        logger.info("Popup trovato (UIA): %s", popup.window_text())
        return popup

    popup = _try_win32(title_re, timeout, poll_interval)
    if popup is not None:
        logger.info("Popup trovato (Win32): %s", popup.window_text())
        return popup

    logger.warning("Popup non trovato entro %s secondi.", timeout)
    return None


# ---------------------------------------------------------------------------
# Click
# ---------------------------------------------------------------------------

def _try_invoke(btn) -> bool:
    """Prova invoke() via UIA, poi click_input() come fallback."""
    try:
        btn.invoke()
        logger.info("Click via invoke() riuscito.")
        return True
    except Exception:
        logger.debug("invoke() non disponibile, provo click_input().")
    try:
        btn.click_input()
        logger.info("Click via click_input() eseguito.")
        return True
    except Exception:
        logger.exception("Anche click_input() fallito.")
    return False


def _click_button_uia(window, button_text: str) -> bool:
    """Cerca e clicca il pulsante via UIA (Accesso per nome, Rol, etc.)."""
    btn_lower = button_text.lower()
    try:
        # 1) Accesso per nome diretto + control_type Button
        try:
            btn = window.child_window(title=button_text, control_type="Button")
            if btn.exists(timeout=0):
                return _try_invoke(btn)
        except Exception:
            pass

        # 2) Qualsiasi controllo con quel testo esatto
        try:
            btn = window.child_window(title=button_text)
            if btn.exists(timeout=0):
                return _try_invoke(btn)
        except Exception:
            pass

        # 3) Case-insensitive: cercaInChildren per nome che contiene il testo
        try:
            btn = window.child_window(title_re=f"(?i){button_text}")
            if btn.exists(timeout=0):
                return _try_invoke(btn)
        except Exception:
            pass

        # 4) Ricorsivo: qualunque elemento visibile con il testo nel nome
        for child in window.descendants():
            try:
                name = (child.window_text() or "").lower()
                if btn_lower in name:
                    return _try_invoke(child)
            except Exception:
                continue

        # 5) Cerca per AutomationId parziale
        for child in window.descendants():
            try:
                aid = (child.element_info.automation_id or "").lower()
                if "continue" in aid or "continua" in aid or "ok" in aid or "accept" in aid:
                    return _try_invoke(child)
            except Exception:
                continue

        # 6) Cerca nel dialog "Esegui flusso" se presente
        try:
            dialog = window.child_window(title_re="(?i)Esegui flusso", control_type="Window")
            if dialog.exists(timeout=0):
                for desc in dialog.descendants():
                    try:
                        name = (desc.window_text() or "").lower()
                        if btn_lower in name:
                            return _try_invoke(desc)
                    except Exception:
                        continue
        except Exception:
            pass

    except Exception:
        logger.exception("Errore ricerca pulsante UIA.")
    return False


def _click_button_win32(window, button_text: str) -> bool:
    """Cerca e clicca il pulsante via Win32 backend."""
    btn_lower = button_text.lower()
    try:
        try:
            btn = window.child_window(title=button_text, class_name="Button")
            if btn.exists(timeout=0):
                return _try_invoke(btn)
        except Exception:
            pass

        try:
            btn = window.child_window(title=button_text)
            if btn.exists(timeout=0):
                return _try_invoke(btn)
        except Exception:
            pass

        try:
            btn = window.child_window(title_re=f"(?i){button_text}")
            if btn.exists(timeout=0):
                return _try_invoke(btn)
        except Exception:
            pass

        for child in window.descendants():
            try:
                name = (child.window_text() or "").lower()
                if btn_lower in name:
                    return _try_invoke(child)
            except Exception:
                continue

        # Cerca per automation_id nei dialog child
        for child in window.descendants():
            try:
                aid = (getattr(child.element_info, "automation_id", "") or "").lower()
                if any(kw in aid for kw in ("continue", "continua", "ok", "accept")):
                    return _try_invoke(child)
            except Exception:
                continue

        # Cerca nel dialog "Esegui flusso" se presente
        try:
            dialog = window.child_window(title_re="(?i)Esegui flusso", class_name="#32770")
            if dialog.exists(timeout=0):
                for desc in dialog.descendants():
                    try:
                        name = (desc.window_text() or "").lower()
                        if btn_lower in name:
                            return _try_invoke(desc)
                    except Exception:
                        continue
        except Exception:
            pass

    except Exception:
        logger.exception("Errore ricerca pulsante Win32.")
    return False


# ---------------------------------------------------------------------------
# Dump diagnostico
# ---------------------------------------------------------------------------

def _dump_control(ctrl, indent: int = 0) -> str:
    """Serializza un singolo controllo pywinauto in una riga leggibile."""
    prefix = "  " * indent
    try:
        text = ctrl.window_text() or ""
        ei = getattr(ctrl, "element_info", None)
        ctype = getattr(ei, "control_type", "?") if ei else "?"
        cls = getattr(ei, "class_name", "?") if ei else "?"
        auto_id = getattr(ei, "automation_id", "?") if ei else "?"
        try:
            r = ctrl.rectangle()
            rect = f"L{r.left},T{r.top},R{r.right},B{r.bottom}"
        except Exception:
            rect = "?"
        return f"{prefix}[{ctype}] class={cls} id='{auto_id}' text='{text}' rect={rect}"
    except Exception as e:
        return f"{prefix}(errore: {e})"


def _dump_window_tree(window) -> list[str]:
    """Restituisce la lista di righe con l'albero completo dei controlli."""
    lines: list[str] = []
    lines.append(_dump_control(window, indent=0))
    try:
        for child in window.descendants():
            lines.append(_dump_control(child, indent=1))
    except Exception as e:
        lines.append(f"  (descendants() fallito: {e})")
    return lines


def _dump_all_visible_windows(backend: str = "uia") -> list[str]:
    """Elenca tutte le finestre visibili con titolo."""
    from pywinauto import Desktop
    lines: list[str] = []
    try:
        desktop = Desktop(backend=backend)
        for w in desktop.windows():
            try:
                if w.is_visible() and w.window_text():
                    ei = w.element_info
                    cls = getattr(ei, "class_name", "?")
                    auto_id = getattr(ei, "automation_id", "?")
                    lines.append(f"  '{w.window_text()}' (class={cls}, id={auto_id})")
            except Exception:
                pass
    except Exception as e:
        lines.append(f"  (errore Desktop: {e})")
    return lines


# ---------------------------------------------------------------------------
# API pubblica
# ---------------------------------------------------------------------------

def click_continue(
    title: str = DEFAULT_POPUP_TITLE,
    button_text: str = DEFAULT_BUTTON_TEXT,
    timeout: float = DEFAULT_POPUP_TIMEOUT,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    lock_timeout: float = 2.0,
) -> bool:
    import re
    from pywinauto import Desktop
    
    logger.info("Ricerca popup '%s' (timeout=%.0fs)...", title, timeout)

    # --- dump finestre visibili al momento della ricerca ---
    logger.info("=== FINESTRE VISIBILI (inizio ricerca) ===")
    for line in _dump_all_visible_windows("uia"):
        logger.info(line)

    title_re = re.compile(re.escape(title), re.IGNORECASE)
    deadline = time.monotonic() + timeout
    
    dumped_handles: set[int] = set()   # dump una sola volta per handle
    last_window = None

    while time.monotonic() < deadline:
        for backend in ["uia", "win32"]:
            try:
                desktop = Desktop(backend=backend)
                windows = desktop.windows(title_re=title_re)
                for popup in windows:
                    if not popup.is_visible():
                        continue

                    last_window = popup

                    # --- dump albero controlli appena trovata ---
                    h = popup.handle
                    if h not in dumped_handles:
                        dumped_handles.add(h)
                        logger.info(
                            "=== POPUP TROVATO (%s) handle=%s ===",
                            backend, h,
                        )
                        for line in _dump_window_tree(popup):
                            logger.info("  TREE: %s", line)

                    try:
                        try:
                            SetForegroundWindow(popup.handle)
                        except Exception:
                            pass
                        
                        with _focus_lock(popup, timeout=lock_timeout):
                            clicked = False
                            if backend == "uia":
                                clicked = _click_button_uia(popup, button_text)
                            else:
                                clicked = _click_button_win32(popup, button_text)

                            if clicked:
                                logger.info(
                                    "Click '%s' eseguito sulla finestra '%s'.",
                                    button_text, popup.window_text(),
                                )
                                return True
                            else:
                                logger.warning(
                                    "Pulsante '%s' NON trovato nella finestra '%s' (backend=%s).",
                                    button_text, popup.window_text(), backend,
                                )
                    except Exception:
                        logger.debug("Errore temporaneo durante il click, riprovo...")
            except Exception:
                pass
                
        time.sleep(poll_interval)

    logger.warning(
        "Popup '%s' o pulsante '%s' non trovato (timeout=%.0fs).",
        title, button_text, timeout,
    )

    # --- dump finale se la finestra esiste ma il pulsante no ---
    if last_window is not None:
        logger.warning("=== DUMP FINALE FINESTRA '%s' ===", last_window.window_text())
        for line in _dump_window_tree(last_window):
            logger.warning("  TREE: %s", line)

    logger.warning("=== FINESTRE VISIBILI (al timeout) ===")
    for line in _dump_all_visible_windows("uia"):
        logger.warning(line)
            
    return False
