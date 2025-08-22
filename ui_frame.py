from ui_docked_undocked import UiDockedUndocked
from ui_navigation import UiNavigationPlane
from ui_multy_planes_widget import MultiPlanesWidget, PlaneSwitch
from ui_table import CanvasTableView

import tkinter as tk
from _logger import logger
from typing import Any, Optional
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

        self._docked_call_after_id = None

        planes = MultiPlanesWidget(
            [SwitchesModes.Cargo, SwitchesModes.Highlighting], self
        )
        self._cargo_table_view = CanvasTableView(
            planes.plane_frames[SwitchesModes.Cargo]
        )
        self._highlights_planes = MultiPlanesWidget(
            [SwitchesModes.Docked, SwitchesModes.Navigated],
            planes.plane_frames[SwitchesModes.Highlighting],
        )

        # Highlights depend on docked state.
        self._docked = UiDockedUndocked(
            self._cargo_table_view,
            self._highlights_planes.plane_frames[SwitchesModes.Docked],
        )
        self._docked.pack(anchor="nw", padx=5, pady=5)

        # Highlights depend on navigation state
        self._navigating = UiNavigationPlane(
            self._cargo_table_view,
            self._highlights_planes.plane_frames[SwitchesModes.Navigated],
        )

        weakself = weakref.ref(self)

        def update():
            obj = weakself()
            if obj:
                obj._cargo_on_carrier_updated()

        fleetcarriercargo.FleetCarrierCargo.add_on_cargo_change_handler(update)

    def _cargo_on_carrier_updated(self):
        logger.debug("Got carrier update signal.")
        self._cargo_table_view.populate_colored_carrier_data()

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
        self._navigating.get_systems_receiver().set_current_system(system)

        logger.debug(f"Received event: {event}")
        if event == "StartUp":
            self._cargo_table_view.populate_colored_carrier_data()
        logger.debug(
            f"Active pane {self._highlights_planes.active_plane_frame}, docking pane {self._docked}."
        )

        # Check if "Docked" plane is activated by user.
        if type(self).is_ancestor(
            self._highlights_planes.active_plane_frame, self._docked
        ):
            logger.debug(f"Active 'Docked' plane, event {event}")
            self._handle_docking_events(event, station or state["StationName"])  # type: ignore

    def _handle_docking_events(self, event: Any, station: str | None):
        """
        Handle docking-related events when the "Docked" plane is active in the GUI.

        Depending on the event type, triggers appropriate updates for the docking state:
        - For "Docked" event, schedules a delayed update to allow market data to be ready.
        - For "StartUp" and "Market", triggers an immediate update.
        - For "Undocked", clears the docked state immediately.
        - Ignores other unrelated events.

        Parameters:
            event (Any): The docking event name as a string.
            station (Optional[str]): The station name relevant to the event.
        """
        if event not in [
            "StartUp",
            "Market",
            "Undocked",
            "Docked",
            "Disembark",
            "Embark",
        ]:
            logger.debug(f"_handle_docking_events: ignoring {event}")
            return
        logger.debug(f"_handle_docking_events: processing {event}, station {station}")

        # If we're here we must stop the timer (depend on event it can be 2 different reasons though).
        if self._docked_call_after_id is not None:
            self.after_cancel(self._docked_call_after_id)
            self._docked_call_after_id = None

        if event == "Undocked":
            self._docked.undocked()
        else:
            # Delayed "docked" because market data file on disk maybe absent yet.
            delay = 1000 if event == "Docked" else 50
            self._docked_call_after_id = self.after(
                delay,
                lambda: setattr(self, "_docked_call_after_id", None)
                or self._docked.docked_to(station),
            )

    @staticmethod
    def is_ancestor(ancestor: tk.Widget, widget: tk.Widget) -> bool:
        current = widget
        while current is not None:  # type: ignore
            if current is ancestor:
                return True
            current = current.master
        return False
