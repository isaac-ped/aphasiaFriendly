from dataclasses import dataclass
import dataclasses
from functools import cache
from typing import Literal
from .caching import localcache
from openai import OpenAI
from openai.types.chat import ChatCompletion

from ..config import Config
from ..logger import logger
import json


@cache
def client():
    return OpenAI(api_key=Config.get().openai_api_key)


@dataclass
class Message:
    content: str
    # Used to ensure that "role" is only ever passed as a keyword
    _: dataclasses.KW_ONLY
    role: Literal["user", "assistant", "system"] = "user"


@localcache
def _completion_api(messages: list[dict], model="gpt-4") -> ChatCompletion:
    """Send a completion request to the OpenAI API."""
    logger.debug(
        "Sending the following prompt: \n"
        + "\n"
        + json.dumps(messages, indent=2)
        + "\n"
    )
    # Idk what type this actually is should be so I'm ignoring it and pretending its a dict
    return client().chat.completions.create(model=model, messages=messages)  # type: ignore


def completion(messages: list[Message], model="gpt-4") -> str:
    """Send a completion request to the OpenAI API and return the text of the response"""
    message_dicts = [dataclasses.asdict(message) for message in messages]
    response = _completion_api(message_dicts, model=model)
    str_response = response.choices[0].message.content
    assert str_response is not None
    return str_response
