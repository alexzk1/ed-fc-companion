# from external_web_search import FilterSellFromEDSM
from ui_base_filter_plane import UiBaseFilteredPlane
from ui_system_input import UiSystemInput, SystemNamesReceiver
from ui_table import CanvasTableView
from _logger import logger


class UiNavigationPlane(UiBaseFilteredPlane):
    def __init__(self, target_table: CanvasTableView, *args, **kwargs):  # type: ignore
        super().__init__(target_table, *args, **kwargs)  # type: ignore

        self._system_input = UiSystemInput(self._user_provided_system_name, self)
        self._system_input.grid(row=0, column=0, sticky="nw", padx=5, pady=5)

    def get_systems_receiver(self) -> SystemNamesReceiver:
        return self._system_input

    def _user_provided_system_name(self, system_name: str):
        logger.debug(f"User selected system: {system_name}")
