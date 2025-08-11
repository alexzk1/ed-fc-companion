from collections import defaultdict
from dataclasses import dataclass
import threading
from typing import Any, Set, TypeAlias
import requests
from _logger import logger
from carrier_cargo_position import CarrierCargoPosition
from sell_on_station import FilterSellOnStationProtocol
from cargo_names import MarketCatalogue


def get_inara_commodity_url(commodity_name: str) -> str | None:
    """
    Gets link-endpoint on / from Inara for the commodity.
    """
    base = "https://inara.cz"
    params = {"type": "GlobalSearch", "term": commodity_name}
    url = f"https://inara.cz/sites/elite/ajaxsearch.php"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://inara.cz/",
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": "gzip",
    }

    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()

    body = response.text
    logger.debug(f"Inara query {response.url} response for link: {body}")

    results = response.json()

    for entry in results:
        label = entry.get("label", "")
        if label.startswith('<a href="/elite/commodity/'):
            href_start = label.find('href="') + 6
            href_end = label.find('"', href_start)
            href = label[href_start:href_end]
            return base + href

    return None


@dataclass
class FilteredStation:
    station_name: str
    station_id: int
    market_id: int


EdsmResponse: TypeAlias = list[dict[str, Any]]
EdsmPerStationTypeResponse: TypeAlias = dict[str, list[FilteredStation]]


class EdsmCachedAccess:
    _mutex = threading.Lock()
    _stations_per_system: dict[str, EdsmPerStationTypeResponse] = {}

    def __init__(self):
        pass

    @classmethod
    def get_stations_in_system(cls, system_name: str) -> EdsmPerStationTypeResponse:
        with cls._mutex:
            if system_name not in cls._stations_per_system:
                cls._stations_per_system[system_name] = cls._filter_and_group_stations(
                    cls.get_edsm_stations_in_system(system_name)
                )
            return cls._stations_per_system[system_name]

    @staticmethod
    def _filter_and_group_stations(
        stations: EdsmResponse,
    ) -> EdsmPerStationTypeResponse:
        grouped: EdsmPerStationTypeResponse = defaultdict(list)

        for station in stations:
            if not station.get("haveMarket", False):
                continue

            station_type = station.get("type", "Unknown")
            filtered_station = FilteredStation(
                station_name=station.get("name", ""),
                station_id=station.get("id", -1),
                market_id=station.get("marketId", -1),
            )
            grouped[station_type].append(filtered_station)

        return grouped

    @staticmethod
    def get_edsm_stations_in_system(system_name: str) -> EdsmResponse:
        if not system_name:
            return []

        BASE_URL = "https://www.edsm.net/api-system-v1/stations"
        params = {
            "systemName": system_name,
        }
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

        return data.get("stations", [])


class FilterSellFromEDSM(FilterSellOnStationProtocol):
    _mutex = threading.Lock()
    # Key is marketId
    _cache_static: dict[int, Set[int]] = {}

    def __init__(self, station: FilteredStation):
        self._station = station
        self.__fetch_station_buys(station)

    def __fetch_station_buys(self, station: FilteredStation) -> None:
        """
        Gets and updates list of what station is buying from EDSM.
        Uses own local in-RAM cache too to relax EDSM.
        """
        key = station.market_id
        with type(self)._mutex:
            if key in self._cache_static:
                self._buy_ids = type(self)._cache_static[key]
                return
        url = "https://www.edsm.net/api-system-v1/stations/market"
        params: dict[str, Any] = {"marketId": station.market_id}

        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()

        buys = {
            commodity_obj.id
            for item in data.get("commodities", [])
            if item.get("demand", 0) > 0 and "id" in item
            for commodity_obj in [MarketCatalogue.explain_commodity(item["id"])]
            if commodity_obj is not None
        }
        with type(self)._mutex:
            if key not in self._cache_static:
                type(self)._cache_static[key] = buys
        self._buy_ids = buys

    def is_not(self, station_name: str) -> bool:
        return self._station.station_name != station_name

    def is_buying(self, what: CarrierCargoPosition) -> bool:
        return what.id in self._buy_ids
