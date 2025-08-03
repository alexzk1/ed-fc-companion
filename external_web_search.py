from typing import Set, Tuple
import requests
from _logger import logger
from carrier_cargo_position import CarrierCargoPosition
from sell_on_station import FilterSellOnStationProtocol


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


class FilterSellFromEDSM(FilterSellOnStationProtocol):
    def __init__(self, system: str, station: str):
        self._system = system
        self._station = station
        self.cache: dict[Tuple[str, str], Set[int]] = {}
        self._buy_ids = self.fetch_station_buys(system, station)

    def fetch_station_buys(self, system: str, station: str) -> Set[int]:
        key = (system, station)
        if key in self.cache:
            return self.cache[key]
        url = (
            "https://www.edsm.net/api-system-v1/stations"
            f"?systemName={system}&stationName={station}&showMarket=1"
        )
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        buys = {
            item["id"]
            for item in data.get("market", {}).get("commodities", [])
            if item.get("demand", 0) > 0 and "id" in item
        }
        self.cache[key] = buys
        return buys

    def is_not(self, station_name: str) -> bool:
        return self._station != station_name

    def is_buying(self, what: CarrierCargoPosition) -> bool:
        return what.id in self._buy_ids
