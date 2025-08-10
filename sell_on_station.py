import json
import os
from typing import Any
from carrier_cargo_position import CarrierCargoPosition
from config import config
import cargo_names
from _logger import logger


class FilterSellOnStationProtocol:
    """
    This is prototype to define filter which checks if commodity stored on carrier can be sold on station.
    """

    def is_buying(self, what: CarrierCargoPosition) -> bool: ...

    """
    Returns True if station related to this filter buys param: what.
    """

    def is_not(self, station_name: str) -> bool: ...

    """
    Station related to this filter is not param: station_name.
    """


class FilterSellOnDockedStation(FilterSellOnStationProtocol):
    def __init__(self, station: str):
        self._station_buys: list[cargo_names.MarketNameWithCommodity] = []
        self._station = station
        self._load_market_json_what_station_buys()

    def is_not(self, station_name: str):
        return self._station != station_name

    def is_buying(self, what: CarrierCargoPosition) -> bool:
        for item in self._station_buys:
            if what.id == item.market.id:
                return True
        return False

    def _load_market_json_what_station_buys(self):
        journal_dir = config.get_str("journaldir")
        if not journal_dir:
            journal_dir = config.default_journal_dir
        file_path = os.path.join(journal_dir, "Market.json")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load Market.json: {e}")
            return

        items: list[dict[str, Any]] = content.get("Items", [])
        for i in items:
            try:
                if int(i.get("Demand", 0)) <= 0:
                    continue
                commodity_id = int(i["id"])
                item = cargo_names.MarketCatalogue.explain_commodity_id(commodity_id)
                if item:
                    self._station_buys.append(item)
            except Exception as e:
                logger.warning(f"Skipping malformed item in Market.json: {i} ({e})")
