from base64 import b64decode
import copy
import json

from pydantic import BaseModel, Field
import requests
from requests_oauthlib import OAuth1

from ..config import Config
from ..logger import logger
from .caching import cache_af

from openai.types.responses import FunctionToolParam


class IconSearchResult(BaseModel):
    id_: str = Field(description="ID for the icon on nounproject")
    tags: list[str] = Field(description="A list of tags associated with this icon")
    collection_names: list[str] = Field(
        description="A list of the collections this icon belongs to"
    )


# Definition of the "search" function as a tool, apporopriate for openAI use
SEARCH_TOOL = FunctionToolParam(
    name="search_nounproject",
    type="function",
    strict=True,
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "A keyword or set of keywords to search for in nounproject's API ",
            },
        },
        "required": [
            "query",
        ],
        "additionalProperties": False,
    },
)


def search(query: str, limit: int = 10) -> list[IconSearchResult]:
    """Search for nounproject icons matching a query

    :param query: The keyword(s) with which to query nounproject
    :param limit: The maximum number of icons to return
    """
    auth = OAuth1(Config.get().nounproject_api_key, Config.get().nounproject_secret)
    endpoint = "https://api.thenounproject.com/v2/icon"

    response = requests.get(
        endpoint,
        auth=auth,
        params={
            "query": query,
            "limit_to_public_domain": 0,
            "include_svg": 0,
            "limit": limit,
        },
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
def get_icon(icon_id: int) -> bytes | None:
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
