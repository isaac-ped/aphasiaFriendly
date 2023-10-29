import dataclasses
import json
import openai
import logging
import click
from . import api_access
from pathlib import Path
from . import prompts
from . import config
from .logger import setup_logging


openai.organization = config.ORGANIZATION_ID
openai.api_key = config.get_api_key()


@click.command()
@click.argument("abstract_file", type=Path)
@click.option("--output", type=Path, default="summary.json")
@click.option("-v", "--verbose", count=True)
def summarize(abstract_file: Path, output: Path, verbose: int):
    """Create an aphasia-friendly summary for an abstract at the given path."""
    setup_logging(verbose)
    messages = [dataclasses.asdict(message) for message in prompts.SUMMARY_MESSAGES]

    logging.info(f"Loading abstract from {abstract_file}")

    messages.append({"role": "user", "content": abstract_file.read_text().strip()})

    logging.debug(
        "Sending the following prompt: \n"
        + "\n"
        + json.dumps(messages, indent=2)
        + "\n"
    )

    logging.info("Sending to OpenAI completion model")
    response = api_access.completion(messages)

    with output.open("w") as f:
        json.dump(response, f, indent=2)

    logging.info(
        "Generated the following output for summary:\n"
        + response["choices"][0]["message"]["content"]
    )

    messages.append(response["choices"][0]["message"])
    messages.extend([dataclasses.asdict(message) for message in prompts.ICON_MESSAGES])

    logging.debug(
        "Sending the following prompt: \n" + "\n" + json.dumps(messages, indent=2)
    )
    response = api_access.completion(messages)

    logging.info(
        "Generated the following output for icons:\n"
        + response["choices"][0]["message"]["content"]
    )


summarize()
