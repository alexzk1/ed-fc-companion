from typing import Any, Optional
from external_web_search import FilterSellFromEDSM
from multy_planes_widget import MultiPlanesWidget
from sell_on_station import FilterSellOnDockedStation
from ui_table import CanvasTableView
import tkinter as tk
from _logger import logger
import fleetcarriercargo
import weakref
from enum import Enum


class TopPlane(str, Enum):
    Cargo = "Cargo"
    Tools = "Tools"


class ToolsPlane(str, Enum):
    Docked = "Docked"
    Navigated = "Navigated"


class MainUiFrame(tk.Frame):
    """
    Simple wrapper - subclass of tk.Frame for CanvasTableView() which does actual reading/drawing.
    This class handles signal "on cargo changed" from carrier.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        planes = MultiPlanesWidget([TopPlane.Cargo, TopPlane.Tools], self)
        self.table_view = CanvasTableView(planes.plane_frames[TopPlane.Cargo])
        tool_planes = MultiPlanesWidget(
            [ToolsPlane.Docked, ToolsPlane.Navigated],
            planes.plane_frames[TopPlane.Tools],
        )

        label = tk.Label(
            tool_planes.plane_frames[ToolsPlane.Docked], text="Tools will go here"
        )
        label.pack(anchor="nw", padx=10, pady=10)

        weakself = weakref.ref(self)

        def update():
            obj = weakself()
            if obj:
                obj._cargo_on_carrier_updated()

        fleetcarriercargo.FleetCarrierCargo.add_on_cargo_change_handler(update)

    def _cargo_on_carrier_updated(self):
        logger.debug("Got carrier update signal.")
        self.table_view.update_from_carrier()

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

        if station and (event == "Market" or event == "StartUp" or event == "Docked"):
            self.table_view.probably_color_market_on_station = (
                FilterSellOnDockedStation(station)
            )
            self.table_view.update_from_carrier()
        elif event == "Undocked":
            self.table_view.probably_color_market_on_station = None
            self.table_view.update_from_carrier()
