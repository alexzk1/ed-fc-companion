# from external_web_search import FilterSellFromEDSM

from ui_station_input import UiStationInput
from ui_system_input import UiSystemInput, SystemNamesReceiver
from ui_multy_planes_widget import MultiPlanesWidget, PlaneSwitch
from ui_table import CanvasTableView
import tkinter as tk
from _logger import logger
import translation


class _NavigationPlanes:
    NavigatedSystemSelect = PlaneSwitch(
        text=translation.ptl("System"),
        tooltip=translation.ptl("System picker."),
        has_button=True,
    )

    NavigatedStationSelect = PlaneSwitch(
        text=translation.ptl("Station"),
        tooltip=translation.ptl("Station picker."),
        # Station selector does not have a button, so user cannot go direct to it.
        has_button=False,
    )


class UiNavigationPlane(tk.Frame):
    """
    Wizard-like component, once user selects system, it switches to stations.
    """

    def __init__(self, target_table: CanvasTableView, master=None, **kwargs):  # type: ignore
        super().__init__(master, **kwargs)  # type: ignore

        # Wizard planes
        self._sys_station_wizard = MultiPlanesWidget(
            [
                _NavigationPlanes.NavigatedSystemSelect,
                _NavigationPlanes.NavigatedStationSelect,
            ],
            self,
        )

        # System selection.
        self._system_input = UiSystemInput(
            self._user_provided_system_name,
            self._sys_station_wizard.plane_frames[
                _NavigationPlanes.NavigatedSystemSelect
            ],
        )

        # Station selection. Once station is selected, component will signal coloring to cargo table.
        self._station_input = UiStationInput(
            target_table,
            self._sys_station_wizard.plane_frames[
                _NavigationPlanes.NavigatedStationSelect
            ],
        )
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid(row=0, column=0, sticky="nsew")

    def get_systems_receiver(self) -> SystemNamesReceiver:
        """
        Provides "new system known" events listener.
        User may do something inside game which generates different systems and those will be sent here.
        """
        return self._system_input

    def _user_provided_system_name(self, system_name: str):
        """
        User finalized system entry on 1st wizard's pane.
        Switching to station selectors.
        """
        system_name = system_name.strip()
        if not system_name:
            return
        logger.debug(f"User selected system: {system_name}")
        self._station_input.set_target_system(system_name)
        self._sys_station_wizard.activate_plane(
            _NavigationPlanes.NavigatedStationSelect
        )
