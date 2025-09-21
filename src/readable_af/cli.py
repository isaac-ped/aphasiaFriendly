import copy
import subprocess
from pathlib import Path
import json

import click

from readable_af.processing.generation import just_run_summary

from .external import caching
from . import api
from .logger import logger, setup_logging
from .model.request import Ctx


@click.group()
def cli():
    pass


@cli.command()
@click.argument("input_file", type=Path)
@click.option("--out", type=Path, help="output directory", default=None)
@click.option(
    "-f",
    "--format",
    "formats",
    type=str,
    help="output format",
    default=["pptx"],
    multiple=True,
)
@click.option(
    "--cache/--no-cache",
    "do_cache",
    default=True,
    help="If --no-cache, ignore cache when generating",
)
@click.option(
    "--open/--no-open",
    "do_open",
    default=True,
    help="Open the output file after generating",
)
@click.option("-v", "--verbose", count=True)
def summarize(
    input_file: Path,
    out: Path,
    formats: list[str],
    do_open: bool,
    do_cache: bool,
    verbose: int = 0,
):
    """Create an aphasia-friendly summary of an academic paper abstract."""
    setup_logging(verbose)
    if not do_cache:
        caching.NO_CACHE = True
    base_ctx = Ctx()
    base_ctx.input.file = input_file
    base_ctx.output_dir = out
    for format in formats:
        ctx = copy.deepcopy(base_ctx)
        logger.info(f"Generating summary for format {format}")
        ctx.output_format = format
        api.summarize(ctx)
        assert ctx.output_file is not None
        if format == "pptx" and do_open:
            subprocess.call(["open", ctx.output_file])
        if format == "gdoc" and do_open:
            assert ctx.output_link is not None
            subprocess.call(["open", ctx.output_link])
        print(f"Generated file {ctx.output_file}")


@cli.command()
@click.argument("input_file", type=Path)
@click.option("--out", type=Path, help="output directory", default=None)
@click.option(
    "-f",
    "--format",
    "formats",
    type=str,
    help="output format",
    default=["pptx"],
    multiple=True,
)
@click.option(
    "--open/--no-open",
    "do_open",
    default=True,
    help="Open the output file after generating",
)
@click.option("-v", "--verbose", count=True)
def rerun(
    input_file: Path, out: Path, formats: list[str], do_open: bool, verbose: int = 0
):
    """Re-run the summary generation process on a previously summarized file."""
    setup_logging(verbose)

    base_ctx = Ctx()
    base_ctx.input.file = input_file
    base_ctx.output_dir = out
    for format in formats:
        ctx = copy.deepcopy(base_ctx)
        logger.info(f"Generating summary for format {format}")
        ctx.output_format = format
        api.rerun(ctx)
        assert ctx.output_file is not None
        if format == "pptx" and do_open:
            subprocess.call(["open", ctx.output_file])
        if format == "gdoc" and do_open:
            assert ctx.output_link is not None
            subprocess.call(["open", ctx.output_link])
        print(f"Generated file {ctx.output_file}")


@cli.command()
@click.argument("input_file", type=Path)
@click.option("-v", "--verbose", count=True)
def test_prompt(input_file: Path, verbose: int = 0):
    """Just run the summary_prompt function and print the output."""
    setup_logging(verbose)
    contents = input_file.read_text()
    response = just_run_summary(contents)
    print(json.dumps(response, indent=2))
