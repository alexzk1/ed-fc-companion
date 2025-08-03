from typing import Any, Optional
from ui_table import CanvasTableView
import tkinter as tk
from _logger import logger
import fleetcarriercargo
import weakref


class MainUiFrame(tk.Frame):
    """
    Simple wrapper - subclass of tk.Frame for CanvasTableView() which does actual reading/drawing.
    This class handles signal "on cargo changed" from carrier.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.columnconfigure(0, weight=1)
        self.grid(sticky=tk.EW)
        self.table_view = CanvasTableView(self)

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
        if event == "SupercruiseTarget" and entry.get("TargetType") == "Station":
            station_name = entry.get("Name")
            station_system = entry.get("System")  # Может не совпадать с текущим system!
            logger.debug(f"Station target selected: {station_name} in {station_system}")
            self.station_target = (station_system, station_name)

        if station and (event == "Market" or event == "StartUp" or event == "Docked"):
            self.table_view.probably_color_market_on_station = station
            self.table_view.update_from_carrier()
        elif event == "Undocked":
            self.table_view.probably_color_market_on_station = None
            self.table_view.update_from_carrier()
