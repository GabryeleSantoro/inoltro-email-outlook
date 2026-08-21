"""Diagnostic: dump the UIA tree of the Power Automate popup.

Run this while the popup is visible::

    python -m inoltro_email.inspect_popup

It prints every control in the window so we can see the exact button
text and control type.
"""

from __future__ import annotations

import sys
import time


def _dump_element(element, indent: int = 0) -> None:
    """Recursive dump of a UIA element and its children."""
    try:
        ctrl = element.element_info
        name = ctrl.name or ""
        ctrl_type = ctrl.control_type or ""
        auto_id = ctrl.automation_id or ""
        class_name = ctrl.class_name or ""
        rect = ctrl.rectangle

        prefix = "  " * indent
        print(
            f"{prefix}[{ctrl_type}] "
            f"name={name!r} "
            f"auto_id={auto_id!r} "
            f"class={class_name!r} "
            f"rect={rect}"
        )
    except Exception as exc:
        print(f"  " * indent + f"<error reading element: {exc}>")
        return

    try:
        for child in element.children():
            _dump_element(child, indent + 1)
    except Exception:
        pass


def main() -> None:
    from pywinauto import Desktop

    print("Cerco finestre 'Power Automate'...\n")

    for backend in ("uia", "win32"):
        print(f"=== Backend: {backend} ===")
        try:
            desktop = Desktop(backend=backend)
            for w in desktop.windows():
                title = w.window_text()
                if "automate" in title.lower() or "power" in title.lower():
                    print(f"\nFinestra: {title!r}")
                    print(f"  handle={w.handle}")
                    print(f"  visible={w.is_visible()}")
                    _dump_element(w, indent=1)
                    print()
        except Exception as exc:
            print(f"  Errore: {exc}\n")

    print("Fatto.")


if __name__ == "__main__":
    main()
