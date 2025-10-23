from pydantic import BaseModel
import json
from functools import cache
from typing import Literal

from openai import OpenAI
from openai.types.chat import ChatCompletion

from ..config import Config
from ..logger import logger
from .caching import cache_af


@cache
def client():
    return OpenAI(api_key=Config.get().openai_api_key)


class Message(BaseModel):
    content: str
    # Used to ensure that "role" is only ever passed as a keyword
    # _: dataclasses.KW_ONLY -> Pydantic doesn't support this, presumably unnecessary
    role: Literal["user", "assistant", "system"] = "user"


@cache_af()
def _completion_api(messages: list[dict], model="gpt-4-1106-preview") -> ChatCompletion:
    """Send a completion request to the OpenAI API."""
    print(len(json.dumps(messages)))
    if len(json.dumps(messages)) > 16384:
        raise ValueError("Hit arbitrary length limit! Messages must be less than 16kb")
    logger.debug(
        "Sending the following prompt: \n"
        + "\n"
        + json.dumps(messages, indent=2)
        + "\n"
    )
    # Idk what type this actually is should be so I'm ignoring it and pretending its a dict
    return client().chat.completions.create(model=model, messages=messages)  # type: ignore


def completion(messages: list[Message], model="gpt-4-1106-preview") -> str:
    """Send a completion request to the OpenAI API and return the text of the response"""
    message_dicts = [message.model_dump() for message in messages]
    response = _completion_api(message_dicts, model=model)
    str_response = response.choices[0].message.content
    assert str_response is not None
    return str_response
