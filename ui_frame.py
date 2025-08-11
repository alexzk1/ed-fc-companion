from typing import Any, Optional
from ui_docked_undocked import UiDockedUndocked
from ui_multy_planes_widget import MultiPlanesWidget, PlaneSwitch

from ui_table import CanvasTableView
import tkinter as tk
from _logger import logger
import fleetcarriercargo
import weakref
import translation


class SwitchesModes:
    Cargo = PlaneSwitch(
        text=translation.ptl("Cargo On Carrier"),
        tooltip=translation.ptl("Shows carrier's cargo."),
    )

    Highlighting = PlaneSwitch(
        text=translation.ptl("Highlighting"),
        tooltip=translation.ptl(
            "Select which station to use for highlighting sellable cargo: the current docked station or the navigation target."
        ),
    )

    Docked = PlaneSwitch(
        text=translation.ptl("Docked"),
        tooltip=translation.ptl("If selected, highlight based on docked station."),
    )

    Navigated = PlaneSwitch(
        text=translation.ptl("Navigated"),
        tooltip=translation.ptl(
            "If selected, use highlight based on current navigation."
        ),
    )


class MainUiFrame(tk.Frame):
    """
    Simple wrapper - subclass of tk.Frame for CanvasTableView() which does actual reading/drawing.
    This class handles signal "on cargo changed" from carrier.
    """

    def __init__(self, *args, **kwargs):  # type: ignore
        super().__init__(*args, **kwargs)  # type: ignore

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        planes = MultiPlanesWidget(
            [SwitchesModes.Cargo, SwitchesModes.Highlighting], self
        )
        self._table_view = CanvasTableView(planes.plane_frames[SwitchesModes.Cargo])
        self._tool_planes = MultiPlanesWidget(
            [SwitchesModes.Docked, SwitchesModes.Navigated],
            planes.plane_frames[SwitchesModes.Highlighting],
        )

        self._docked = UiDockedUndocked(
            self._table_view, self._tool_planes.plane_frames[SwitchesModes.Docked]
        )
        self._docked.pack(anchor="nw", padx=10, pady=10)

        weakself = weakref.ref(self)

        def update():
            obj = weakself()
            if obj:
                obj._cargo_on_carrier_updated()

        fleetcarriercargo.FleetCarrierCargo.add_on_cargo_change_handler(update)

    def _cargo_on_carrier_updated(self):
        logger.debug("Got carrier update signal.")
        self._table_view.populate_colored_carrier_data()

    def journal_entry(
        self,
        cmdr: str,
        is_beta: bool,
        system: Optional[str],
        station: Optional[str],
        entry: dict[str, Any],
        state: dict[str, Any],
    ):
        event = entry.get("event")
        logger.debug(f"Received event: {event}")
        if event == "StartUp":
            self._table_view.populate_colored_carrier_data()
        logger.debug(
            f"Active pane {self._tool_planes.active_plane_frame}, docking pane {self._docked}."
        )
        if type(self).is_ancestor(self._tool_planes.active_plane_frame, self._docked):
            logger.debug(f"Active 'Docked' plane, event {event}")
            self._handle_docking_events(event, station)

    def _handle_docking_events(self, event: Any, station: str | None):
        if not hasattr(self, "_docked_call_after_id"):
            self._docked_call_after_id = None

        if event in ("StartUp", "Market", "Undocked"):
            if self._docked_call_after_id is not None:
                self.after_cancel(self._docked_call_after_id)
                self._docked_call_after_id = None

            if event == "Undocked":
                self._docked.undocked()
            else:
                self._do_docked_to(station)

        elif event == "Docked":
            if self._docked_call_after_id is not None:
                self.after_cancel(self._docked_call_after_id)

            self._docked_call_after_id = self.after(
                1000, lambda: self._do_docked_to(station)
            )

    def _do_docked_to(self, station: str | None):
        self._docked_call_after_id = None
        self._docked.docked_to(station)

    @staticmethod
    def is_ancestor(ancestor: tk.Widget, widget: tk.Widget) -> bool:
        current = widget
        while current is not None:  # type: ignore
            if current is ancestor:
                return True
            current = current.master
        return False
