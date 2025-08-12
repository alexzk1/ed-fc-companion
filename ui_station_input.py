from external_web_search import EdsmCachedAccess, EdsmPerStationTypeResponse
from ui_base_filter_plane import UiBaseFilteredPlane
from ui_table import CanvasTableView
import threading
import queue
from _logger import logger


class UiStationInput(UiBaseFilteredPlane):
    def __init__(self, target_table: CanvasTableView, master=None, **kwargs):  # type: ignore
        super().__init__(target_table, master, **kwargs)  # type: ignore

        self._edsm_data_queue: queue.Queue[EdsmPerStationTypeResponse] = queue.Queue(
            maxsize=5
        )
        self.grid(row=0, column=0, sticky="nw", padx=3, pady=3)
        self._process_queue_scheduled = False
        self._check_retries: int = 0

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
        pass
