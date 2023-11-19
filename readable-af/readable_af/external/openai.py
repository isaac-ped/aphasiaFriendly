from dataclasses import dataclass
import dataclasses
from typing import Literal
from .caching import localcache
import openai
from ..config import Config
from ..logger import logger
import json


@dataclass
class Message:
    content: str
    # Used to ensure that "role" is only ever passed as a keyword
    _: dataclasses.KW_ONLY
    role: Literal["user", "assistant", "system"] = "user"

    def __post_init__(self):
        self.content = self.content.strip()
        self.content = self.content.replace("\n", " ")


@localcache
def _completion_api(messages: list[dict], model="gpt-4") -> dict:
    """Send a completion request to the OpenAI API."""
    openai.organization = Config.openai_org_id
    openai.api_key = Config.openai_api_key
    logger.debug(
        "Sending the following prompt: \n"
        + "\n"
        + json.dumps(messages, indent=2)
        + "\n"
    )
    # Idk what type this actually is should be so I'm ignoring it and pretending its a dict
    return openai.ChatCompletion.create(model=model, messages=message_dicts)  # type: ignore


def completion(messages: list[Message], model="gpt-4") -> str:
    """Send a completion request to the OpenAI API and return the text of the response"""
    message_dicts = [dataclasses.asdict(message) for message in messages]
    response = _completion_api(message_dicts, model=model)
    return response["choices"][0]["message"]["content"]
