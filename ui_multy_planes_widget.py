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
    has_button: bool = True


@dataclass
class _SinglePlane:
    panel: tk.Frame
    button: Optional[tk.Button]


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

    def __init__(
        self,
        planes: list[PlaneSwitch],
        parent: tk.Widget,
        **kwargs,  # type: ignore
    ):
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
        self.grid(row=0, column=0, sticky=tk.NSEW)

        # Buttons panel.
        self._buttons_frame: Optional[tk.Frame] = None
        for plane in planes:
            if plane.has_button:
                self._buttons_frame = tk.Frame(self)
                self._buttons_frame.grid(row=0, column=0, sticky=tk.NW)
                break

        self._planes: dict[str, _SinglePlane] = {}
        self._selected_plane: str = ""

        for plane in planes:
            name = plane.text
            panel = tk.Frame(self)
            panel.grid(row=1, column=0, sticky=tk.NSEW)
            panel.grid_rowconfigure(0, weight=1)
            panel.grid_columnconfigure(0, weight=1)

            button: Optional[tk.Button] = None
            if plane.has_button:
                button = tk.Button(
                    self._buttons_frame,
                    text=name,
                    command=lambda n=name: self.activate_plane(n),
                )
                button.grid(row=0, column=len(self._planes), sticky=tk.NW)
                if plane.tooltip:
                    Tooltip(button, plane.tooltip)
            self._planes[name] = _SinglePlane(panel=panel, button=button)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        if planes and len(planes) > 0:
            self.activate_plane(planes[0])

    def activate_plane(self, plane_name: str | PlaneSwitch):
        """
        Activates plane by given name.
        """
        name: str = (
            plane_name.text if isinstance(plane_name, PlaneSwitch) else plane_name
        )

        selected_plane = self._planes.get(name, None)
        if selected_plane:
            self._selected_plane = name
            for plane in self._planes.values():
                if plane.button:
                    plane.button.config(relief=tk.RAISED, state=tk.NORMAL)
                plane.panel.grid_remove()
            if selected_plane.button:
                selected_plane.button.config(relief=tk.SUNKEN, state=tk.DISABLED)
            selected_plane.panel.grid(row=1, column=0, sticky=tk.NSEW)

    @property
    def plane_frames(self) -> Mapping[str | PlaneSwitch, tk.Frame]:
        return MultiPlanesWidget._PlaneDictView(self._planes)

    @property
    def active_plane_frame(self) -> tk.Frame:
        logger.debug(
            f"Active pane: {self._selected_plane} ({self.plane_frames[self._selected_plane]})"
        )
        return self.plane_frames[self._selected_plane]
