"""This file wraps openai access with a simple local cache
so we can play around with subsequent stepes assuming the pipeline remains
the same up until that point"""

import json
from .caching import localcache

import openai

from .config import Config
from .logger import logger


@localcache
def completion(messages: list[dict], model="gpt-4") -> dict:
    openai.organization = Config.openai_org_id
    openai.api_key = Config.openai_api_key
    logger.debug(
        "Sending the following prompt: \n"
        + "\n"
        + json.dumps(messages, indent=2)
        + "\n"
    )
    # Idk what type this actually is should be so I'm ignoring it and pretending its a dict
    return openai.ChatCompletion.create(model=model, messages=messages)  # type: ignore
