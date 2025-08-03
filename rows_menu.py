import tkinter as tk
from cargo_names import MarketName
from _logger import logger


class RightClickContextMenuForTable:
    def __init__(
        self, parent: tk.Widget, market: MarketName, amount: int, commodity: str
    ):
        self._parent = parent
        self._market = market
        self._amount = amount
        self._commodity = commodity

        self._menu = tk.Menu(self._parent, tearoff=0)
        self._build_menu()

    def _build_menu(self):
        self._menu.add_command(
            label=f"Copy: {self._commodity}", command=self._copy_commodity
        )
        self._menu.add_command(
            label=f"Show market: {self._market}", command=self._show_market_info
        )
        self._menu.add_separator()
        self._menu.add_command(label="Debug info", command=self._log_debug_info)

    def _copy_commodity(self):
        self._parent.clipboard_clear()
        self._parent.clipboard_append(self._commodity)

    def _show_market_info(self):
        logger.info(f"Market info requested: {self._market}")
        # TODO

    def _log_debug_info(self):
        logger.debug(
            f"Commodity: {self._commodity}, Market: {self._market}, Amount: {self._amount}"
        )

    def popup(self, event: tk.Event):
        try:
            self._menu.tk_popup(event.x_root, event.y_root)
        finally:
            self._menu.grab_release()
