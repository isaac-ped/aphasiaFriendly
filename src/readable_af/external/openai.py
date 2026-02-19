from pydantic import BaseModel
import json
from functools import cache
from typing import Literal, TypeVar, Type, Any

from openai import OpenAI
from openai.types.chat import ChatCompletion
import openai

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
    role: Literal["user", "assistant", "system", "tool"] = "user"


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


def _handle_function_call(
    function_name: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    """Handle function calls from OpenAI.

    Args:
        function_name: Name of the function to call
        arguments: Arguments for the function

    Returns:
        Result of the function call as a dict
    """
    logger.debug(f"Handling function call: {function_name} with arguments: {arguments}")

    if function_name == "get_icon":
        # Create Pydantic model from arguments
        params = nounproject.GetIconParams(**arguments)
        # Call the function
        result = nounproject._get_icon_function(params)
        # Convert result to dict for JSON serialization
        return result.model_dump()

    return {"error": f"Unknown function: {function_name}"}


def completion_structured(
    messages: list[Message], response_model: Type[T], model: str = "gpt-4o-2024-08-06"
) -> T:
    """Send a completion request with structured output and function calling support.

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

    # Try creating tool with just the function - pydantic_function_tool may infer everything
    # Type ignore: pydantic_function_tool may not be in type stubs
    try:
        get_icon_tool = openai.pydantic_function_tool(nounproject._get_icon_function)  # type: ignore
        tools = [get_icon_tool]
    except (TypeError, AttributeError) as e:
        logger.warning(f"Could not create function tool: {e}. Function calling disabled.")
        tools = None

    message_dicts = [message.model_dump() for message in messages]
    max_iterations = 10  # Prevent infinite loops
    iteration = 0

    try:
        while iteration < max_iterations:
            # Call API directly with structured output and function calling
            parse_kwargs = {
                "model": model,
                "input": json.dumps(message_dicts),
                "text_format": response_model,
            }
            if tools is not None:
                parse_kwargs["tools"] = tools
            response = client().responses.parse(**parse_kwargs)

            if response.error is not None:
                raise ValueError(
                    f"OpenAI API returned an error: {response.error.message}"
                )

            # Check if the model wants to call a function
            # The responses.parse API may return tool calls in the response
            # Type ignore: tool_calls may exist at runtime even if not in type definition
            tool_calls = None
            if hasattr(response, "tool_calls") and response.tool_calls:  # type: ignore
                tool_calls = response.tool_calls  # type: ignore
            elif hasattr(response, "output") and hasattr(response.output, "tool_calls"):  # type: ignore
                tool_calls = response.output.tool_calls  # type: ignore

            if response.output_parsed is None and tool_calls:
                # Handle function calls
                for tool_call in tool_calls:
                    # Handle different possible structures of tool_call
                    if hasattr(tool_call, "function"):
                        function_name = tool_call.function.name
                        function_args = (
                            json.loads(tool_call.function.arguments)
                            if isinstance(tool_call.function.arguments, str)
                            else tool_call.function.arguments
                        )
                        tool_call_id = (
                            tool_call.id if hasattr(tool_call, "id") else None
                        )
                    elif isinstance(tool_call, dict):
                        function_name = tool_call.get("function", {}).get("name", "")
                        function_args = tool_call.get("function", {}).get(
                            "arguments", {}
                        )
                        if isinstance(function_args, str):
                            function_args = json.loads(function_args)
                        tool_call_id = tool_call.get("id")
                    else:
                        logger.warning(f"Unexpected tool_call structure: {tool_call}")
                        continue

                    # Execute the function
                    function_result = _handle_function_call(
                        function_name, function_args
                    )

                    # Add function result to messages
                    tool_message = {
                        "role": "tool",
                        "content": json.dumps(function_result),
                    }
                    if tool_call_id:
                        tool_message["tool_call_id"] = tool_call_id
                    message_dicts.append(tool_message)

                iteration += 1
                continue

            # If we have a parsed output, return it
            if response.output_parsed is not None:
                return response.output_parsed

            # If we get here, something went wrong
            raise ValueError("Failed to parse structured output from OpenAI API")

        raise ValueError(
            f"Exceeded maximum iterations ({max_iterations}) for function calling"
        )

    except Exception as e:
        logger.error(f"Failed to get structured output from OpenAI API: {e}")
        raise
