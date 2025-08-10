from dataclasses import dataclass
import tkinter as tk
from collections.abc import Iterator, Mapping
from typing import Optional
from _logger import logger
from ui_tooltip import Tooltip


@dataclass(frozen=True)
class PlaneSwitch:
    """
    Describes plane switches (buttons).
    """

    text: str
    tooltip: Optional[str] = None


@dataclass
class _SinglePlane:
    panel: tk.Frame
    button: tk.Button


class MultiPlanesWidget(tk.Frame):
    """
    This widget provides a way to organize others into different planes switched by buttons.
    """

    class _PlaneDictView(Mapping):  # pyright: ignore[reportMissingTypeArgument]
        def __init__(self, source: dict[str, _SinglePlane]):
            self._source = source

        def __getitem__(self, key: str | PlaneSwitch) -> tk.Frame:
            if isinstance(key, PlaneSwitch):
                key = key.text
            return self._source[key].panel

        def __iter__(self) -> Iterator[str]:
            return iter(self._source)

        def __len__(self) -> int:
            return len(self._source)

        def __contains__(self, key: object) -> bool:
            return key in self._source

    def __init__(self, planes: list[PlaneSwitch], parent: tk.Widget, **kwargs):  # type: ignore
        """
        Initialize MultiPlanesWidget.

        Args:
            planes (list[PlaneSwitch]): List of PlaneSwitch. Each button will have one of string as the text on it.
                            Each name will have dedicated frame accessed over .plane_frames["name"]
                            where children can be placed.
                            When button is pressed corresponding plane is visible and others are invisible.
            parent (tk.Widget): Must support free resizings inside, you may want to call
                            parent.columnconfigure(0, weight=1)
                            parent.rowconfigure(1, weight=1)
        """
        super().__init__(parent, **kwargs)  # pyright: ignore[reportUnknownArgumentType]
        self.grid(row=0, column=0, sticky=tk.EW)

        self.__planes: dict[str, _SinglePlane] = {}
        self._selected_plane: str = ""

        for plane in planes:
            name = plane.text
            panel = tk.Frame(parent)
            panel.grid(row=1, column=0, sticky=tk.NSEW)
            panel.grid_rowconfigure(0, weight=1)
            panel.grid_columnconfigure(0, weight=1)
            button = tk.Button(
                self,
                text=name,
                command=lambda n=name: self._process_pane_button_click(n),
            )
            button.grid(row=0, column=len(self.__planes), sticky=tk.EW)
            if plane.tooltip:
                Tooltip(button, plane.tooltip)
            self.__planes[name] = _SinglePlane(panel=panel, button=button)
        if planes and len(planes) > 0:
            self._process_pane_button_click(planes[0].text)

    def _process_pane_button_click(self, name: str):
        selected_plane = self.__planes.get(name, None)
        if selected_plane:
            self._selected_plane = name
            for plane in self.__planes.values():
                plane.button.config(relief=tk.RAISED, state=tk.NORMAL)
                plane.panel.grid_remove()
            selected_plane.button.config(relief=tk.SUNKEN, state=tk.DISABLED)
            selected_plane.panel.grid()

    @property
    def plane_frames(self) -> Mapping[str | PlaneSwitch, tk.Frame]:
        return MultiPlanesWidget._PlaneDictView(self.__planes)

    @property
    def active_plane_frame(self) -> tk.Frame:
        logger.debug(
            f"Active pane: {self._selected_plane} ({self.plane_frames[self._selected_plane]})"
        )
        return self.plane_frames[self._selected_plane]
