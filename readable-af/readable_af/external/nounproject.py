import json
from ..config import Config
from requests_oauthlib import OAuth1
from .caching import localcache
from ..model.summary import Icon
import requests


def search(query: str, n: int) -> list[Icon]:
    """Search for an icon matching a query. Return None if no icons are found."""
    icon_ids = _find_icon_ids(query)
    if not icon_ids:
        return []
    icons: list[Icon] = []
    for _ in range(n):
        icon_id = icon_ids[0]
        icon_url = _get_icon_url(icon_id)
        icon = _get_icon(icon_url)
        icons.append(Icon(query, icon_url, icon, icon_id))
    return icons


@localcache
def _find_icon_ids(query: str) -> list[int]:
    """Search for icons matching a keyword.

    :param query: A term to search for in nounproject
    :returns: A list of IDs for icons that match the query
    """
    auth = OAuth1(Config.get().nounproject_api_key, Config.get().nounproject_secret)
    endpoint = "https://api.thenounproject.com/v2/icon"

    response = requests.get(endpoint, auth=auth, params={"query": query})
    content = json.loads(response.content.decode("utf-8"))
    if "icons" not in content:
        return []
    return [icon["id"] for icon in content["icons"]]


@localcache
def _get_icon_url(icon_id: int) -> str:
    """Given an icon ID, get the URL for the icon

    :param icon_id: An ID for a nounproject icon (returned from search_icons)
    :returns: The URL for the provided icon
    """
    cfg = Config.get()
    auth = OAuth1(cfg.nounproject_api_key, cfg.nounproject_secret)
    endpoint = f"https://api.thenounproject.com/v2/icon/{icon_id}"

    response = requests.get(endpoint, auth=auth)
    content = json.loads(response.content.decode("utf-8"))
    return content["icon"]["thumbnail_url"]


@localcache
def _get_icon(icon_url: str) -> bytes:
    """Given an icon URL, get the icon itself"""
    return requests.get(icon_url).content
