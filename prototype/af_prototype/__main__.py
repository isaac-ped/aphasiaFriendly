import dataclasses
from pathlib import Path
from af_prototype.icon_req import display_svg_icon, get_icon_url, search_icons

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

    abstract_contents = response["choices"][0]["message"]["content"]
    logger.info(f"Extracted abstract from provided input:\n{abstract_contents}")

    logger.info("Generating summary")
    messages = prompts.asdict(prompts.SUMMARY_MESSAGES)
    messages.append({"role": "user", "content": abstract_contents})

    response = api_access.completion(messages)
    summary = response["choices"][0]["message"]["content"]
    logger.info(f"Generated a summary from the provided abstract:\n{summary}")

    messages = prompts.asdict(prompts.SUMMARY_MESSAGES)
    messages.append(response["choices"][0]["message"])
    messages.extend([dataclasses.asdict(message) for message in prompts.ICON_MESSAGES])
    response = api_access.completion(messages)

    keyword_lines = response["choices"][0]["message"]["content"]
    logger.info(f"Generated a list of keywords for icons:\n{keyword_lines}")

    for keyword_line, summary_line in zip(keyword_lines.split("\n"), summary.split("\n")):
        print(f"**********\n{summary_line}")
        print(f"Keywords: {keyword_line}")
        for keyword in keyword_line.split(","):
            keyword = keyword.strip("- ,")
            icon_ids = search_icons(keyword)
            if len(icon_ids) > 0:
                url = get_icon_url(icon_ids[0])
                display_svg_icon(url, True)


@cli.command()
@click.argument("pdf_file", type=Path)
@click.option("--output", type=Path)
@click.option("-v", "--verbose", count=True, default=1)
def extract_sections(pdf_file: Path, output: Path | None, verbose: int):
    """Attempt to extract sections from a PDF file."""
    setup_logging(verbose)

    if not output:
        # Remove the .pdf extension
        output = pdf_file.with_suffix("")

    extract_abstract(pdf_file, output)


@cli.command()
@click.argument("search_term", type=str)
@click.option("-n", type=int, default=5)
@click.option("--invert/--no-invert", help="Invert the icon colors")
@click.option("-v", "--verbose", count=True, default=1)
def search_nounproject(search_term: str, n: int, verbose: int, invert: bool):
    """Search for icons in nounproject based on keyword. Display in terminal."""
    setup_logging(verbose)
    ids = search_icons(search_term)
    for id in ids[:n]:
        url = get_icon_url(id)
        display_svg_icon(url, invert)


if __name__ == "__main__":
    cli()
