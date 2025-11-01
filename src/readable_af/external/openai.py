from pydantic import BaseModel
import json
from functools import cache
from typing import Literal, TypeVar, Type

from openai import OpenAI
from openai.types.chat import ChatCompletion

from ..config import Config
from ..logger import logger
from .caching import cache_af

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


def _add_additional_properties_false(schema: dict) -> dict:
    """Recursively add additionalProperties: false to all object schemas and ensure
    all properties are in the required array (for OpenAI strict mode).

    OpenAI's structured output API requires:
    1. additionalProperties to be explicitly set to false for all object types
    2. When using strict mode, ALL properties must be in the required array

    Args:
        schema: JSON schema dictionary to modify

    Returns:
        Modified schema with additionalProperties: false added and required arrays fixed
    """
    schema = schema.copy()  # Don't mutate the original

    # Skip processing if this is a $ref (references are handled via $defs)
    if "$ref" in schema:
        return schema

    # If this is an object type, add additionalProperties: false
    if schema.get("type") == "object":
        schema["additionalProperties"] = False

        # For OpenAI strict mode, ALL properties must be in required array
        if "properties" in schema:
            # Ensure required array exists and contains all properties
            if "required" not in schema:
                schema["required"] = []

            # Add any missing properties to required array
            required_set = set(schema["required"])
            for prop_name in schema["properties"].keys():
                if prop_name not in required_set:
                    schema["required"].append(prop_name)

            # Recursively process properties
            for prop_name, prop_schema in schema["properties"].items():
                if isinstance(prop_schema, dict):
                    schema["properties"][prop_name] = _add_additional_properties_false(
                        prop_schema
                    )

        # Recursively process items in array properties
        if "items" in schema:
            if isinstance(schema["items"], dict):
                schema["items"] = _add_additional_properties_false(schema["items"])

    # Process $defs if present (do this before other processing to handle refs)
    if "$defs" in schema:
        for def_name, def_schema in schema["$defs"].items():
            if isinstance(def_schema, dict):
                schema["$defs"][def_name] = _add_additional_properties_false(def_schema)

    # Process anyOf, oneOf, allOf if present
    for key in ["anyOf", "oneOf", "allOf"]:
        if key in schema:
            schema[key] = [
                _add_additional_properties_false(item)
                if isinstance(item, dict)
                else item
                for item in schema[key]
            ]

    return schema


def completion(messages: list[Message], model: str = "gpt-4-1106-preview") -> str:
    """Send a completion request to the OpenAI API and return the text of the response"""
    message_dicts = [message.model_dump() for message in messages]
    response = _completion_api(message_dicts, model=model)
    str_response = response.choices[0].message.content
    assert str_response is not None
    return str_response


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
    message_dicts = [message.model_dump() for message in messages]

    # Generate JSON schema from Pydantic model
    json_schema = response_model.model_json_schema()

    # OpenAI requires additionalProperties: false for all object schemas
    json_schema = _add_additional_properties_false(json_schema)

    # Remove title from schema if present (OpenAI doesn't need it)
    schema_for_api = {k: v for k, v in json_schema.items() if k != "title"}

    # Create response format for structured output
    # The "name" should be a unique identifier for the schema (alphanumeric + underscores)
    model_name = (
        response_model.__name__ if hasattr(response_model, "__name__") else "response"
    )
    # Ensure name is a valid identifier (alphanumeric + underscores, no spaces/special chars)
    schema_name = "".join(c if c.isalnum() or c == "_" else "_" for c in model_name)
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": schema_name.lower(),
            "schema": schema_for_api,
            "strict": True,  # Enforce strict adherence to the schema
        },
    }

    logger.debug(
        f"Using structured output with schema: {json.dumps(schema_for_api, indent=2)}"
    )

    # Log the request (similar to _completion_api)
    logger.debug(
        "Sending the following prompt: \n"
        + "\n"
        + json.dumps(message_dicts, indent=2)
        + "\n"
    )

    try:
        # Call API directly with structured output (not using _completion_api to avoid modifying it)
        response = client().chat.completions.create(
            model=model,
            messages=message_dicts,  # type: ignore
            response_format=response_format,  # type: ignore
        )
    except Exception as e:
        logger.error(f"Failed to get structured output from OpenAI API: {e}")
        raise

    # Parse the structured output
    response_content = response.choices[0].message.content
    if response_content is None:
        raise ValueError("No content in structured output response")

    try:
        # Parse and validate with Pydantic
        response_data = json.loads(response_content)
        return response_model.model_validate(response_data)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from structured output: {response_content}")
        raise ValueError(f"Invalid JSON in structured output: {e}") from e
    except Exception as e:
        logger.error(
            f"Failed to validate structured output against model {response_model.__name__}: {e}"
        )
        raise ValueError(f"Validation failed: {e}") from e
