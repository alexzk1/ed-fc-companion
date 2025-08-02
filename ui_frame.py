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
