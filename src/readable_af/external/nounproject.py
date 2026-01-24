from base64 import b64decode
import copy
import json
import keyword

from pydantic import BaseModel, Field
import requests
from requests_oauthlib import OAuth1

from ..config import Config
from ..logger import logger
from ..model.summary import Icon
from .caching import cache_af


# This is the ID for an icon on nounproject that we're using as a filler icon for the moment
QUESTION_MARK_ID: int = 5525618


def set_to_default(icon: Icon):
    """Used if we can't find any icons for a keyword.
    Sets the icon to the QUESTION_MARK icon with some accompanying text
    """
    contents = _get_icon(QUESTION_MARK_ID)
    if contents is not None:
        icon.populate("", contents, QUESTION_MARK_ID)


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
        logger.info("Fetching icon %s for %s", icon_id, icon.keyword)
        # icon_url = _get_icon_url(icon_id)
        contents = _get_icon(icon_id)
        if contents is None:
            blacklist.add(icon_id)
            continue
        icon.populate("", contents, icon_id)
        logger.info(f"Using icon {icon_id} for {icon}")
        # blacklist.add(icon_id)
        return True
    logger.warning(f"Used all of the icons for keyword {keyword}. Skipping")
    return False


class IconSearchResult(BaseModel):
    id_: str = Field(description="ID for the icon on nounproject")
    tags: list[str] = Field(description="A list of tags associated with this icon")
    collection_names: list[str] = Field(
        description="A list of the collections this icon belongs to"
    )


def search(query: str, limit: int = 20) -> list[IconSearchResult]:
    """Search for nounproject icons matching a query"""
    auth = OAuth1(Config.get().nounproject_api_key, Config.get().nounproject_secret)
    endpoint = "https://api.thenounproject.com/v2/icon"

    response = requests.get(
        endpoint,
        auth=auth,
        params={"query": query, "limit_to_public_domain": 0, "include_svg": 0, "limit": limit},
    )
    content = json.loads(response.content.decode("utf-8"))
    if "icons" not in content:
        return []
    return [
        IconSearchResult(
            id_=icon["id"],
            tags=icon["tags"],
            collection_names=[collection["name"] for collection in icon["collections"]],
        )
        for icon in content["icons"]
    ]


@cache_af(version="2")
def _find_icon_ids(query: str) -> list[int]:
    """Search for icons matching a keyword.

    :param query: A term to search for in nounproject
    :returns: A list of IDs for icons that match the query
    """
    auth = OAuth1(Config.get().nounproject_api_key, Config.get().nounproject_secret)
    endpoint = "https://api.thenounproject.com/v2/icon"

    response = requests.get(
        endpoint,
        auth=auth,
        params={"query": query, "limit_to_public_domain": 0, "include_svg": 0},
    )
    content = json.loads(response.content.decode("utf-8"))
    if "icons" not in content:
        return []
    ids = [icon["id"] for icon in content["icons"]]
    logger.debug(f"Found the following ids: {ids}")
    return ids


@cache_af(version="2", verify_fn=lambda x: x is not None)
def _get_icon(icon_id: int) -> bytes | None:
    """Given an icon URL, get the icon itself"""
    cfg = Config.get()
    auth = OAuth1(cfg.nounproject_api_key, cfg.nounproject_secret)
    endpoint = f"https://api.thenounproject.com/v2/icon/{icon_id}/download"
    response = requests.get(
        endpoint, auth=auth, params={"color": "000000", "filetype": "png", "size": 100}
    )
    try:
        content = json.loads(response.content.decode("utf-8"))
    except Exception as e:
        logger.error(f"Error decoding response: {e}\n{response.content}")
        return None
    logger.debug(f"Got response with keys {content.keys()} from {endpoint}")
    dbg = copy.deepcopy(content)
    dbg["base64_encoded_file"] = "..."
    logger.debug(f"Response: {dbg}")
    if "base64_encoded_file" not in content:
        return None

    return b64decode(content["base64_encoded_file"])
