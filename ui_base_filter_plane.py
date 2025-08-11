from typing import Optional
from sell_on_station import FilterSellOnStationProtocol
import tkinter as tk
from ui_table import CanvasTableView


class UiBaseFilteredPlane(tk.Frame):
    """
    Base UI class which contains target_table and current_highlighter for it.
    """

    def __init__(self, target_table: CanvasTableView, master=None, **kwargs):  # type: ignore
        super().__init__(master, **kwargs)  # type: ignore
        self.columnconfigure(0, weight=1)

        self._target_table_view: CanvasTableView = target_table
        self._current_highlight_filter: Optional[FilterSellOnStationProtocol] = None

    def _activate_current_highlighter(self):
        self._target_table_view.set_cargo_highlighter(self._current_highlight_filter)

    def _set_current_highlighter(self, what: Optional[FilterSellOnStationProtocol]):
        self._current_highlight_filter = what
