import requests
from _logger import logger


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
