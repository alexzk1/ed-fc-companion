import tkinter as tk
from typing import Callable
from cargo_names import MarketName
from _logger import logger


class _MenuCommand:
    def __init__(self, label: str, handler: Callable[[], None]):
        self.label = label
        self.handler = handler


class _MenuSeparator:
    """Marker class to insert separator into menu."""

    pass


class RightClickContextMenuForTable:
    def __init__(
        self, parent: tk.Widget, market: MarketName, amount: int, commodity: str
    ):
        self._parent = parent
        self._market = market
        self._amount = amount
        self._commodity = commodity

        self._menu = tk.Menu(self._parent, tearoff=0)

        self._commands: list[_MenuCommand | _MenuSeparator] = [
            _MenuCommand(
                f"Copy: {self._market.trade_name}",
                lambda: self._copy_to_clipboard(self._market.trade_name),
            ),
            _MenuSeparator(),
            _MenuCommand(f"Cancel: {self._market.trade_name}", lambda: None),
        ]

        self._build_menu()

    def popup(self, event: tk.Event):
        try:
            self._menu.tk_popup(event.x_root, event.y_root)
        finally:
            self._menu.grab_release()

    def _build_menu(self):
        for cmd in self._commands:
            if isinstance(cmd, _MenuCommand):
                self._menu.add_command(label=cmd.label, command=cmd.handler)
            else:
                self._menu.add_separator()

    def _copy_to_clipboard(self, text: str):
        self._parent.clipboard_clear()
        self._parent.clipboard_append(text)
