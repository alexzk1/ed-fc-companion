from typing import Any, Optional
from external_web_search import FilterSellFromEDSM
from sell_on_station import FilterSellOnDockedStation
from ui_table import CanvasTableView
import tkinter as tk
from _logger import logger
import fleetcarriercargo
import weakref
from tkinter import ttk


class MainUiFrame(tk.Frame):
    """
    Simple wrapper - subclass of tk.Frame for CanvasTableView() which does actual reading/drawing.
    This class handles signal "on cargo changed" from carrier.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)  # panel area

        switcher = tk.Frame(self)
        switcher.grid(row=0, column=0, sticky=tk.EW)
        self.btn_cargo = tk.Button(switcher, text="Cargo", command=self.show_cargo)
        self.btn_tools = tk.Button(switcher, text="Tools", command=self.show_tools)
        self.btn_cargo.pack(side=tk.LEFT, padx=2, pady=2)
        self.btn_tools.pack(side=tk.LEFT, padx=2, pady=2)

        # Cargo
        self.panel_cargo = tk.Frame(self)
        self.panel_cargo.grid(row=1, column=0, sticky=tk.NSEW)
        self.panel_cargo.grid_rowconfigure(0, weight=1)
        self.panel_cargo.grid_columnconfigure(0, weight=1)
        self.table_view = CanvasTableView(self.panel_cargo)

        # Tools
        self.panel_tools = tk.Frame(self)
        self.panel_tools.grid(row=1, column=0, sticky=tk.NSEW)
        label = tk.Label(self.panel_tools, text="Tools will go here")
        label.pack(anchor="nw", padx=10, pady=10)

        # Initial opened
        self.show_cargo()

        weakself = weakref.ref(self)

        def update():
            obj = weakself()
            if obj:
                obj._cargo_on_carrier_updated()

        fleetcarriercargo.FleetCarrierCargo.add_on_cargo_change_handler(update)

    def show_cargo(self):
        self.panel_tools.grid_remove()
        self.panel_cargo.grid()

        self.btn_cargo.config(relief=tk.SUNKEN, state=tk.DISABLED)
        self.btn_tools.config(relief=tk.RAISED, state=tk.NORMAL)

    def show_tools(self):
        self.panel_cargo.grid_remove()
        self.panel_tools.grid()

        self.btn_tools.config(relief=tk.SUNKEN, state=tk.DISABLED)
        self.btn_cargo.config(relief=tk.RAISED, state=tk.NORMAL)

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
