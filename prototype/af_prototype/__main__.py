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
    """Create an aphasia-friendly summary of an academic paper abstract."""
    setup_logging(verbose)

    # Check if is pdf file
    if input_file.suffix == ".pdf":
        logger.info(f"Extracting abstract from {input_file}")
        abstract_contents = extract_abstract(input_file, None)
    else:
        logger.info(f"Loading abstract from {input_file}")
        abstract_contents = input_file.read_text().strip()

    messages = prompts.asdict(prompts.ABSTRACT_EXTRACTION)
    messages.append({"role": "user", "content": abstract_contents})
    response = api_access.completion(messages)
    logger.info("Generated a summary from the provided abstract:")
    print(response["choices"][0]["message"]["content"])

    abstract_contents = response["choices"][0]["message"]["content"]
    logger.info(f"Extracted abstract from provided input:")
    print(abstract_contents)

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


@cli.command()
@click.argument("pdf_file", type=Path)
@click.option("--output", type=Path)
@click.option("-v", "--verbose", count=True)
def extract_sections(pdf_file: Path, output: Path | None, verbose: int):
    """Attempt to extract sections from a PDF file."""
    setup_logging(verbose)

    if not output:
        # Remove the .pdf extension
        output = pdf_file.with_suffix("")

    extract_abstract(pdf_file, output)


if __name__ == "__main__":
    cli()
