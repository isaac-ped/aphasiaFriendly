from .caching import localcache
from ..model.summary import Icon
import requests


def search(query: str) -> Icon | None:
    """Search for an icon matching a query. Return None if no icons are found."""
    icon_ids = _find_icon_ids(query)
    if not icon_ids:
        return None
    icon_id = icon_ids[0]
    icon_url = _get_icon_url(icon_id)
    icon = _get_icon(icon_url)
    return Icon(query, icon_url, icon, icon_id)


@localcache
def _find_icon_ids(query: str) -> list[int]:
    """Search for icons matching a keyword.

    :param query: A term to search for in nounproject
    :returns: A list of IDs for icons that match the query
    """
    ...


@localcache
def _get_icon_url(icon_id: int) -> str:
    """Given an icon ID, get the URL for the icon

    :param icon_id: An ID for a nounproject icon (returned from search_icons)
    :returns: The URL for the provided icon
    """
    ...


@localcache
def _get_icon(icon_url: str) -> bytes:
    """Given an icon URL, get the icon itself"""
    return requests.get(icon_url).content
