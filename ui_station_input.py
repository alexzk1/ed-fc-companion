from typing import Any, Optional
from external_web_search import (
    EdsmCachedAccess,
    EdsmPerStationTypeResponse,
    FilterSellFromEDSM,
    FilteredStation,
)
from ui_base_filter_plane import UiBaseFilteredPlane
from ui_multy_planes_widget import MultiPlanesWidget, PlaneSwitch
from ui_table import CanvasTableView
import threading
import queue
from _logger import logger
import translation
import tkinter as tk


class UiStationInput(UiBaseFilteredPlane):
    def __init__(self, target_table: CanvasTableView, master=None, **kwargs):  # type: ignore
        super().__init__(target_table, master, **kwargs)  # type: ignore

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self._edsm_data_queue: queue.Queue[EdsmPerStationTypeResponse] = queue.Queue(
            maxsize=5
        )

        self._process_queue_scheduled = False
        self._check_retries: int = 0
        self._visible_stations: Optional[MultiPlanesWidget] = None

    def _fetch_stations_thread(self, system_name: str):
        stations = EdsmCachedAccess.get_stations_in_system(system_name)
        self._edsm_data_queue.put(stations)

    def set_target_system(self, system_name: str):
        """Called when user has selected the system."""
        if not self._process_queue_scheduled:
            threading.Thread(
                target=self._fetch_stations_thread, args=(system_name,), daemon=True
            ).start()
            self._check_retries = 0
            self._delayed_check_in_ui_thread()

    def _receive_edsm_data_in_ui_thread(self):
        self._check_retries += 1
        try:
            stations = self._edsm_data_queue.get_nowait()
        except queue.Empty:
            self._delayed_check_in_ui_thread()
            return
        self._process_queue_scheduled = False
        self._update_ui_with_stations(stations)

    def _delayed_check_in_ui_thread(self):
        if self._check_retries > 60:
            self._process_queue_scheduled = False
            logger.error(
                f"Something went wrong, couldn't read EDSM data in {self._check_retries} retries."
            )
            return
        self._process_queue_scheduled = True
        self.after(100, self._receive_edsm_data_in_ui_thread)

    def _update_ui_with_stations(self, stations: EdsmPerStationTypeResponse):
        """
        Now we have all stations from EDSM. Time to update UI.
        """
        logger.debug(
            f"Got list of the stations in the system of {len(stations)} categories."
        )
        if self._visible_stations:
            self._visible_stations.destroy()
            self._visible_stations = None

        # Remaping ports' categories to some shorter ones.
        mapped_types = {
            mapped
            for pt in stations
            if (mapped := type(self).map_station_type(pt)) and mapped[0]
        }
        planes_by_type = [PlaneSwitch(pt[0], pt[1]) for pt in sorted(mapped_types)]
        self._visible_stations = MultiPlanesWidget(planes_by_type, self)

        stations_per_ui_name: dict[str, list[FilteredStation]] = {}
        for category, category_stations in stations.items():
            ui_name, _ = type(self).map_station_type(category)
            stations_per_ui_name.setdefault(ui_name, []).extend(category_stations)

        for ui_name, stations_list in stations_per_ui_name.items():
            stations_per_ui_name[ui_name] = sorted(
                stations_list, key=lambda s: s.station_name
            )

        for ui_name, category_stations in stations_per_ui_name.items():
            frame = self._visible_stations.plane_frames[ui_name]
            listbox = tk.Listbox(frame)
            scrollbar = tk.Scrollbar(
                frame,
                orient=tk.VERTICAL,
                command=listbox.yview,  # type: ignore
            )
            listbox.config(yscrollcommand=scrollbar.set)
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            listbox._stations_objects = category_stations  # type: ignore

            for st in category_stations:
                listbox.insert(tk.END, st.station_name)
            listbox.bind("<<ListboxSelect>>", self._on_station_select)
        self.grid(row=0, column=0, sticky="nsew", padx=3, pady=3)

    def _on_station_select(self, event: Any):
        widget = event.widget
        selection = widget.curselection()
        if selection and widget._stations_objects is not None:
            index = selection[0]
            station_obj = widget._stations_objects[index]  # type: ignore

            def worker():
                highlighter = FilterSellFromEDSM(station_obj)
                self.after(0, lambda: self._apply_highlighter(highlighter))

            threading.Thread(target=worker, daemon=True).start()

    def _apply_highlighter(self, highlighter: FilterSellFromEDSM):
        self._set_current_highlighter(highlighter)
        self._activate_current_highlighter()

    @staticmethod
    def map_station_type(port_type: str) -> tuple[str, str]:
        # TODO: return empty string "" to exclude port_type
        if (
            "Starport" in port_type
            or port_type == "Outpost"
            or port_type == "Mega ship"
        ):
            return translation.ptl("1.In Space"), translation.ptl(
                "Orbital stations, outposts, and mega ships."
            )
        if "Planetary" in port_type:
            return translation.ptl("2.Planetary"), translation.ptl(
                "Horizon's planetary ports and outposts."
            )
        if port_type == "Odyssey Settlement":
            return translation.ptl("3.Settlement"), translation.ptl(
                "Odessey Planetary Settlements."
            )

        if port_type == "Fleet Carrier":
            return translation.ptl("4.Players' FCs"), translation.ptl(
                "Player rented Fleet Carriers."
            )

        return port_type, ""
