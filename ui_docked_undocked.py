import tkinter as tk
from tkinter import ttk
from typing import Optional
from _logger import logger
from ui_base_filter_plane import UiBaseFilteredPlane
from ui_table import CanvasTableView
import carrier_helpers
import translation
from sell_on_station import FilterSellOnDockedStation
from ui_tooltip import Tooltip
import fleetcarriercargo


class UiDockedUndocked(UiBaseFilteredPlane):
    """
    This is pane handles "show for each dock" and "keep showing for current dock".
    """

    _normal_button_text: str = translation.ptl("Highlight for Current Station")

    def __init__(self, target_table: CanvasTableView, *args, **kwargs):  # type: ignore
        """
        Pane that handles:
        - 'follow dock' mode (auto filter on dock)
        - 'freeze' mode (manual apply for current station)
        """
        super().__init__(target_table, *args, **kwargs)  # type: ignore

        self.follow_var = tk.BooleanVar(value=False)
        cb = ttk.Checkbutton(
            self, text=translation.ptl("Highlight on Dock"), variable=self.follow_var
        )
        cb.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        Tooltip(
            cb,
            translation.ptl(
                "Update highlighting on each new docking to just docked market."
            ),
        )

        self._freeze_btn = ttk.Button(
            self,
            text=UiDockedUndocked._normal_button_text,
            command=self._freeze_on_click,
        )
        self._freeze_btn.grid(row=1, column=0, sticky="w", padx=5, pady=5)
        Tooltip(
            self._freeze_btn,
            translation.ptl(
                "Show highlighting for the current station until changed explicit."
            ),
        )
        self._frozen = False

        self._update_btn = ttk.Button(
            self,
            text=translation.ptl("Get Crew Report"),
            command=self._update_fc_on_click,
        )
        self._update_btn.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        Tooltip(
            self._update_btn,
            translation.ptl(
                "Requests a report from the carrier's crew about all current cargo when you're docked on own carrier."
            ),
        )
        self._update_btn.state(["disabled"])  # type: ignore

    def docked_to(self, station: Optional[str]):
        if not station:
            logger.debug("Called docked_to() without station name, ignoring.")
            return
        self._update_buttons(station)
        self._set_current_highlighter(FilterSellOnDockedStation(station))

        if self.follow_var.get():
            # Follow mode: create & install filter immediately
            self._activate_current_highlighter()
            self._frozen = False

    def undocked(self) -> None:
        self._update_buttons(None)
        if self.follow_var.get() or not self._frozen:
            # Follow mode: remove filter on undock
            self._activate_current_highlighter()

    def _update_buttons(self, station: str | None):
        """Change Freeze button depend if we're docked properly."""

        is_carrier: bool = station == carrier_helpers.get_carrier_name()
        is_wrong_station = not station or is_carrier
        logger.debug(
            f"updating freeze button, station {station}, wrong_station: {is_wrong_station} "
        )
        if is_wrong_station:
            self._freeze_btn.state(["disabled"])  # type: ignore
            if is_carrier:
                self._update_btn.state(["!disabled"])  # type: ignore
            self._freeze_btn.config(text=translation.ptl("Wrong Station"))
        else:
            self._update_btn.state(["disabled"])  # type: ignore
            self._freeze_btn.state(["!disabled"])  # type: ignore
            self._freeze_btn.config(text=UiDockedUndocked._normal_button_text)

    def _freeze_on_click(self):
        """Apply filter for current station once and disable follow mode."""

        self.follow_var.set(False)

        if not self._current_highlight_filter:
            logger.warning(
                "It is unexpected that button could be pressed without _current_filter set."
            )
            return
        self._activate_current_highlighter()
        self._frozen = True

    def _update_fc_on_click(self):
        fleetcarriercargo.FleetCarrierCargo.update_from_server()
