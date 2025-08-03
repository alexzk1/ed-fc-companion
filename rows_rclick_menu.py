import tkinter as tk
from typing import Callable
import webbrowser
from cargo_names import MarketName
import fleetcarriercargo
from inara_search import get_inara_commodity_url


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
            _MenuCommand(
                "Check on Inara",
                lambda: self._open_inara_search(self._market.trade_name),
            ),
            _MenuSeparator(),
            _MenuCommand("Cancel/Close", lambda: None),
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

    def _open_inara_search(self, commodity_market_name: str):
        """
        Opens Inara search for buying or selling the given commodity.
        Uses the carrier's current location as search center.
        """

        if not commodity_market_name:
            return
        url = get_inara_commodity_url(commodity_market_name)
        if not url:
            return

        type(self).open_url(url)

    @staticmethod
    def open_url(url: str):
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"Failed to open browser: {e}")
