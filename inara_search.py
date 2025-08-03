import gzip
import io
import urllib.parse
import json
from _logger import logger
import urllib.request


def get_inara_commodity_url(commodity_name: str) -> str | None:
    """
    Gets link-endpoint on / from Inara for the commodity.
    """
    base = "https://inara.cz"
    query = urllib.parse.urlencode({"type": "GlobalSearch", "term": commodity_name})
    url = f"https://inara.cz/sites/elite/ajaxsearch.php?{query}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://inara.cz/",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding": "gzip",
        },
    )
    with urllib.request.urlopen(req) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        if response.info().get("Content-Encoding") == "gzip":
            compressed = response.read()
            with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as gz:
                body = gz.read().decode(charset)
        else:
            body = response.read().decode(charset)

        logger.debug(f"Inara query {url} response for link: {body}")
        results = json.loads(body)
        for entry in results:
            if entry.get("label", "").startswith('<a href="/elite/commodity/'):
                href_start = entry["label"].find('href="') + 6
                href_end = entry["label"].find('"', href_start)
                href = entry["label"][href_start:href_end]
                return base + href

    return None
