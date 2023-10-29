import dataclasses
from pathlib import Path

import click
import openai

from . import api_access, config, prompts
from .fuzzy_finding import extract_abstract
from .logger import logger, setup_logging

openai.organization = config.ORGANIZATION_ID
openai.api_key = config.get_api_key()


@click.group()
def cli():
    pass


@cli.command()
@click.argument("input_file", type=Path)
@click.option("-v", "--verbose", count=True)
def summarize(input_file: Path, verbose: int):
    """Create an aphasia-friendly summary for an abstract at the given path."""
    setup_logging(verbose)

    logger.info(f"Loading abstract from {input_file}")
    abstract_contents = input_file.read_text().strip()

    logger.info("Generating summary")
    messages = prompts.asdict(prompts.SUMMARY_MESSAGES)
    messages.append({"role": "user", "content": abstract_contents})

    response = api_access.completion(messages)
    logger.info("Generated a summary from the provided abstract:")
    print(response["choices"][0]["message"]["content"])

    messages = prompts.asdict(prompts.SUMMARY_MESSAGES)
    messages.append(response["choices"][0]["message"])
    messages.extend([dataclasses.asdict(message) for message in prompts.ICON_MESSAGES])
    response = api_access.completion(messages)

    logger.info("Generated a list of keywords for icons:")
    print(response["choices"][0]["message"]["content"])


if __name__ == "__main__":
    cli()
