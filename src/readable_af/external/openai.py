from pydantic import BaseModel
import json
from functools import cache
from typing import Literal, TypeVar, Type

from openai import OpenAI
from openai.types.chat import ChatCompletion

from ..config import Config
from ..logger import logger
from .caching import cache_af
from . import nounproject

T = TypeVar("T", bound=BaseModel)


@cache
def client():
    return OpenAI(api_key=Config.get().openai_api_key)


class Message(BaseModel):
    content: str
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


def completion(messages: list[Message], model: str = "gpt-4-1106-preview") -> str:
    """Send a completion request to the OpenAI API and return the text of the response"""
    message_dicts = [message.model_dump() for message in messages]
    response = _completion_api(message_dicts, model=model)
    str_response = response.choices[0].message.content
    assert str_response is not None
    return str_response

# The maximum number of times that openai can ask us to use a function on its behalf
MAX_FUNCTION_CALLING_ITERATIONS=20

def completion_structured(
    messages: list[Message], response_model: Type[T], model: str = "gpt-4o-2024-08-06"
) -> T:
    """Send a completion request with structured output.

    Args:
        messages: List of messages to send to the API
        response_model: Pydantic model class that defines the expected response structure
        model: Model to use (must support structured output, e.g. gpt-4o-2024-08-06)

    Returns:
        An instance of response_model validated against the structured output

    Raises:
        ValueError: If the response cannot be parsed or validated
    """

    logger.debug(f"Using structured output with model: {response_model.__name__}")

    message_dicts = [message.model_dump() for message in messages]

    try:
        # Call API directly with structured output (not using _completion_api to avoid modifying it)
        response = client().responses.parse(
            model=model,
            input=json.dumps(message_dicts),
            text_format=response_model,
            tools=[nounproject.SEARCH_TOOL],
        )
    except Exception as e:
        logger.error(f"Failed to get structured output from OpenAI API: {e}")
        raise

    if response.error is not None:
        raise ValueError(f"OpenAI API returned an error: {response.error.message}")

    response_iterations = 0
    while response.output_parsed is None:
        response_iterations += 1
        logger.info(f"looping for {response_iterations}th time")
        if response_iterations > MAX_FUNCTION_CALLING_ITERATIONS:
            raise ValueError(f"No definitive response recieved in {MAX_FUNCTION_CALLING_ITERATIONS} iterations")

        # If any output from the response requested a function call,
        # call that function and make a subsequent request to openAI
        # with the result of calling that function
        for item in response.output:
            if (
                item.type == "function_call"
            ): 
                if (
                    item.name == "search_nounproject"
                ): 
                    arguments = json.loads(item.arguments)
                    rtn = nounproject.search(**arguments)

                    logger.info(
                        f"searched nounproject with arguments {arguments} with response {rtn}"
                    )

                    rtn_dict = [r.model_dump() for r in rtn]
                    message_dicts.append(
                        {
                            "type": "function_call_output",
                            "call_id": item.call_id,
                            "output": json.dumps(rtn_dict),
                        }
                    )

        response = client().responses.parse(
            model=model,
            input=json.dumps(message_dicts),
            text_format=response_model,
            tools=[nounproject.SEARCH_TOOL],
        )

    return response.output_parsed
