"""Use the nounproject API to search for and retrieve icons"""
import json
import subprocess

import requests
from requests_oauthlib import OAuth1

from .api_access import localcache
from .config import nounproject_api_key, nounproject_secret


@localcache
def search_icons(query: str) -> list[int]:
    """Search for icons on nounproject.
    
    :param query: A term to search for in nounproject
    :returns: A list of IDs for icons that match the query
    """
    auth = OAuth1(nounproject_api_key(), nounproject_secret())
    endpoint = "https://api.thenounproject.com/v2/icon"

    response = requests.get(endpoint, auth=auth, params={"query": query})
    content = json.loads(response.content.decode("utf-8"))
    if "icons" not in content:
        return []
    return [icon["id"] for icon in content["icons"]]


@localcache
def get_icon_url(icon_id: int) -> str:
    """Given an icon ID, get the URL for the icon
    
    :param icon_id: An ID for a nounproject icon (returned from search_icons)
    :returns: The URL for the provided icon
    """
    auth = OAuth1(nounproject_api_key(), nounproject_secret())
    endpoint = f"https://api.thenounproject.com/v2/icon/{icon_id}"

    response = requests.get(endpoint, auth=auth)
    content = json.loads(response.content.decode("utf-8"))
    return content["icon"]["thumbnail_url"]


@localcache
def get_icon(icon_url: int) -> bytes:
    """Given an icon URL, get the icon itself"""
    return requests.get(icon_url).content


def display_svg_icon(url: str, invert: bool):
    """Display the icon in the terminal.

    This function is solely for debugging.
    It requires running an iterm2 terminal so imgcat works properly

    :param url: The url of the icon to display
    :param invert: If true, invert the icon (for use with dark background)
    """
    icon = get_icon(url)
    args = [
        "convert",
        "-resize",
        "300x300",
    ]
    # If the background is dark, invert the icon
    if invert:
        # Weird way you have to invert the icon to keep transparenecy
        args.extend(
            [
                "-alpha",
                "deactivate",
                "-negate",
                "-alpha",
                "activate",
            ]
        )
    args.extend(["-background", "none", "-", "png:-"])
    conversion = subprocess.Popen(
        args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    out, _ = conversion.communicate(icon)
    subprocess.Popen(["imgcat"], stdin=subprocess.PIPE).communicate(out)

