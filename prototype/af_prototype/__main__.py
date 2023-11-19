import dataclasses
from pathlib import Path
import subprocess

import click
import openai

from . import api_access, config, prompts
from .fuzzy_finding import extract_abstract, extract_metadata
from .logger import logger, setup_logging
from .nounproject import display_svg_icon, get_icon_url, search_icons, get_icon


@click.group()
def cli():
    pass


@cli.command()
@click.argument("input_file", type=Path)
@click.option(
    "--images/--no-images",
    default=True,
    help="If you are not in iterm2, provide --no-images to suppress the in-terminal display of images from nounproject",
)
@click.option("--out", type=Path, help="output directory", default=None)
@click.option("-v", "--verbose", count=True)
def summarize(input_file: Path, verbose: int, images: bool, out: Path | None = None):
    """Create an aphasia-friendly summary of an academic paper abstract."""
    setup_logging(verbose)

    # Check if is pdf file
    if input_file.suffix == ".pdf":
        logger.info(f"Extracting abstract from {input_file}")
        abstract_contents = extract_abstract(input_file, None)
        metadata_contents = extract_metadata(input_file, None)
    else:
        logger.info(f"Loading abstract from {input_file}")
        abstract_contents = input_file.read_text().strip()
        metadata_contents = None

    messages = prompts.asdict(prompts.ABSTRACT_EXTRACTION)
    messages.append({"role": "user", "content": abstract_contents})
    response = api_access.completion(messages, model="gpt-4")

    abstract_contents = response["choices"][0]["message"]["content"]
    logger.info(f"Extracted abstract from provided input:\n{abstract_contents}")

    if metadata_contents is not None:
        messages = prompts.asdict(prompts.TITLE_AND_AUTHOR_ABSTRACTION)
        messages.append({"role": "user", "content": metadata_contents})
        response = api_access.completion(messages, model="gpt-4")
        metadata_contents = response["choices"][0]["message"]["content"]
        logger.info(f"Extracted metadata from provided input:\n{metadata_contents}")
        metadata_contents = metadata_contents.strip()
        title, authors, date = metadata_contents.split("\n")
    else:
        title, authors, date = "", "", ""

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

    if out is None:
        out = Path("./output") / input_file.stem
    out.mkdir(exist_ok=True, parents=True)
    out_file = out / "summary.md"
    with out_file.open("w") as f:
        f.write(f"% {title}\n")
        f.write(f"% {authors}\n")
        f.write(f"% {date}\n")
        for keyword_line, summary_line in zip(
            keyword_lines.split("\n"), summary.split("\n")
        ):
            print(f"**********\n{summary_line}")
            print(f"Keywords: {keyword_line}")
            f.write(f"\n\n###  {summary_line.strip('- ')}\n")
            f.write("\n:::::::::::::: {.columns}")
            for keyword in keyword_line.split(","):
                keyword = keyword.strip("- ,")
                icon_ids = search_icons(keyword)
                if len(icon_ids) > 0:
                    url = get_icon_url(icon_ids[0])
                    with (out / f"{keyword}.png").open("wb") as fi:
                        fi.write(get_icon(url))
                    f.write('\n\n::: {.column width="40%"}')
                    f.write(f"\n![{keyword}](./{keyword}.png)\n")
                    f.write("\n:::")

                    if images:
                        display_svg_icon(url, True)
                    else:
                        print(f"Image url: {url}")
            f.write("\n::::::::::::::")

    subprocess.check_call(
        ["pandoc", "-t", "pptx", "-s", "summary.md", "-o", "summary.pptx"], cwd=str(out)
    )
    subprocess.check_call(
        ["open", (out / "summary.pptx")],
    )


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
    """Search for icons in nounproject based on keyword. Display in terminal.

    NOTE: This won't work unless you're using iterm2 and are in the nix environment
    that has imgcat installed.
    """
    setup_logging(verbose)
    ids = search_icons(search_term)
    for id in ids[:n]:
        url = get_icon_url(id)
        display_svg_icon(url, invert)


if __name__ == "__main__":
    cli()
