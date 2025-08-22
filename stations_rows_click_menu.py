import tkinter as tk
from typing import Callable
import webbrowser
from external_web_search import (
    FilteredEdsmStation,
    get_inara_station_link,
)
import translation


class _MenuCommand:
    def __init__(self, label: str, handler: Callable[[], None]):
        self.label = label
        self.handler = handler


class _MenuSeparator:
    """Marker class to insert separator into menu."""

    pass


class RightClickContextMenuForStationsList:
    def __init__(self, parent: tk.Widget, clicked_station: FilteredEdsmStation):
        self._parent = parent
        self._clicked_station: FilteredEdsmStation = clicked_station
        self._menu = tk.Menu(self._parent, tearoff=0)

        self._commands: list[_MenuCommand | _MenuSeparator] = [
            _MenuCommand(
                translation.ptl(f"Copy: {self._clicked_station.station_name}"),
                lambda: self._copy_to_clipboard(self._clicked_station.station_name),
            ),
            _MenuCommand(
                translation.ptl("Check on Inara"),
                lambda: self._open_inara_search(self._clicked_station),
            ),
            _MenuSeparator(),
            _MenuCommand(translation.ptl("Cancel/Close"), lambda: None),
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

    def _open_inara_search(self, station: FilteredEdsmStation):
        """
        Opens Inara search for buying or selling the given commodity.
        Uses the carrier's current location as search center.
        """
        if not station:
            return
        url = get_inara_station_link(station)
        if not url:
            return
        type(self).open_url(url)

    @staticmethod
    def open_url(url: str):
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"Failed to open browser: {e}")
