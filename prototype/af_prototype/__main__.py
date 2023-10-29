import dataclasses
import json
import openai
import logging
import click
from . import api_access
from pathlib import Path
from . import prompts
from . import config


openai.organization = config.ORGANIZATION_ID
openai.api_key = config.get_api_key()


@click.command()
@click.argument("abstract_file", type=Path)
@click.option("--output", type=Path, default="summary.json")
@click.option("-v", "--verbose", count=True)
def summarize(abstract_file: Path, output: Path, verbose: int):
    """Create an aphasia-friendly summary for an abstract at the given path."""

    if verbose == 0:
        logging.basicConfig(level=logging.INFO)
    elif verbose > 0:
        logging.basicConfig(level=logging.DEBUG)

    messages = [dataclasses.asdict(message) for message in prompts.SUMMARY_MESSAGES]

    print(f"Loading abstract from {abstract_file}")

    messages.append({"role": "user", "content": abstract_file.read_text().strip()})

    logging.debug(
        "Sending the following prompt: \n"
        + ("=" * 30)
        + "\n"
        + json.dumps(messages, indent=2)
        + "\n"
        + ("=" * 30)
    )

    print("Sending to OpenAI completion model")
    response = api_access.completion(messages)

    with output.open("w") as f:
        json.dump(response, f, indent=2)

    print("Generated the following output:\n" + ("=" * 10))
    print(response["choices"][0]["message"]["content"])


summarize()
