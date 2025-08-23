from collections import defaultdict
from dataclasses import dataclass
import threading
from typing import Any, ClassVar, Set, TypeAlias
import requests
from _logger import logger
from carrier_cargo_position import CarrierCargoPosition
from sell_on_station import FilterSellOnStationProtocol
from cargo_names import MarketCatalogue
import carrier_helpers
import translation
import re


def _call_inara_search(what: str):
    params = {"type": "GlobalSearch", "term": what}
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

    return response.json()


def get_inara_commodity_url(commodity_name: str) -> str | None:
    """
    Gets link-endpoint on / from Inara for the commodity.
    """
    base = "https://inara.cz"
    results = _call_inara_search(commodity_name)
    for entry in results:
        label = entry.get("label", "")
        if label.startswith('<a href="/elite/commodity/'):
            href_start = label.find('href="') + 6
            href_end = label.find('"', href_start)
            href = label[href_start:href_end]
            return base + href

    return None


@dataclass
class FilteredEdsmStation:
    station_name: str
    station_id: int
    market_id: int
    pads_information: str
    system_name: str

    _mutex: ClassVar[threading.Lock] = threading.Lock()
    _cached_inara: ClassVar[dict[str, str]] = {}

    def get_inara_station_link(self) -> str | None:
        base = "https://inara.cz"
        target_key = f"{self.station_name} | {self.system_name}"
        with type(self)._mutex:
            if target_key in type(self)._cached_inara:
                return type(self)._cached_inara[target_key]

        results = _call_inara_search(self.station_name)
        for entry in results:
            if entry.get("value") == target_key:
                # Label has reference like <a href="/elite/station/734697/">
                m = re.search(
                    r'href="([^"]+)"', entry["label"], re.IGNORECASE | re.DOTALL
                )
                if m:
                    url = f"{base}{m.group(1)}"
                    with type(self)._mutex:
                        if target_key not in type(self)._cached_inara:
                            type(self)._cached_inara[target_key] = url
                    return url
        return None


EdsmResponse: TypeAlias = list[dict[str, Any]]
EdsmPerStationTypeResponse: TypeAlias = dict[str, list[FilteredEdsmStation]]


class EdsmCachedAccess:
    _mutex = threading.Lock()
    _stations_per_system: dict[str, EdsmPerStationTypeResponse] = {}

    def __init__(self):
        pass

    @classmethod
    def get_stations_in_system(cls, system_name: str) -> EdsmPerStationTypeResponse:
        """
        Returns processed list of the stations for out limited purposes, groupped by station's type.
        """
        with cls._mutex:
            if system_name not in cls._stations_per_system:
                cls._stations_per_system[system_name] = cls._filter_and_group_stations(
                    cls.get_raw_edsm_stations_in_system(system_name), system_name
                )
            return cls._stations_per_system[system_name]

    @staticmethod
    def _filter_and_group_stations(
        stations: EdsmResponse, system: str
    ) -> EdsmPerStationTypeResponse:
        grouped: EdsmPerStationTypeResponse = defaultdict(list)
        carrier_name = carrier_helpers.get_carrier_name()

        for station in stations:
            if not station.get("haveMarket", False):
                continue

            station_type = station.get("type", "Unknown")
            filtered_station = FilteredEdsmStation(
                station_name=station.get("name", ""),
                station_id=station.get("id", -1),
                market_id=station.get("marketId", -1),
                pads_information="",
                system_name=system,
            )
            if filtered_station.station_name == carrier_name:
                continue
            logger.debug(f"station type: {station_type}")
            if station_type == "Outpost":
                filtered_station.pads_information = translation.ptl("outpost")
            grouped[station_type].append(filtered_station)

        return grouped

    @staticmethod
    def get_raw_edsm_stations_in_system(system_name: str) -> EdsmResponse:
        """
        Returns raw response from EDSM as json object.
        """
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

    def __init__(self, station: FilteredEdsmStation):
        self._station = station
        self.__fetch_station_buys(station)

    def __fetch_station_buys(self, station: FilteredEdsmStation) -> None:
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

        # EDSM gives string "commodity" as "id" field. We want to parse numeric ID out of it.
        buys = {
            commodity_obj.id
            for item in data.get("commodities", [])
            if item.get("stock", 0) == 0 and item.get("demand", 0) > 0 and "id" in item
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
