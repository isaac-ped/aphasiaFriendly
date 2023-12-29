import json
import keyword

import requests
from requests_oauthlib import OAuth1

from ..config import Config
from ..logger import logger
from ..model.summary import Icon
from .caching import localcache


def populate(icon: Icon, blacklist: set[int]) -> bool:
    """Populate an icon containing a keyword with its image data.
    :returns: True if the icon was successfully populated. False if keyword search failed.
    """
    icon_ids = _find_icon_ids(icon.keyword)
    if not icon_ids:
        logger.debug(f"Could not find any icons for keyword {icon.keyword}")
        return False
    for icon_id in icon_ids:
        if icon_id in blacklist:
            logger.debug(f"Skipping icon {icon_id}")
            continue
        icon_url = _get_icon_url(icon_id)
        contents = _get_icon(icon_url)
        icon.populate(icon_url, contents, icon_id)
        logger.info(f"Using icon {icon_url} for {icon}")
        blacklist.add(icon_id)
        return True
    logger.warning(f"Used all of the icons for keyword {keyword}. Skipping")
    return False


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
