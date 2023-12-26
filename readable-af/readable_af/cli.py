import copy
import subprocess
from pathlib import Path

import click

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
@click.option("-v", "--verbose", count=True)
def summarize(input_file: Path, out: Path, formats: list[str], verbose: int = 0):
    """Create an aphasia-friendly summary of an academic paper abstract."""
    setup_logging(verbose)

    base_ctx = Ctx()
    base_ctx.input.file = input_file
    base_ctx.output_dir = out
    for format in formats:
        ctx = copy.deepcopy(base_ctx)
        logger.info(f"Generating summary for format {format}")
        ctx.output_format = format
        api.summarize(ctx)
        assert ctx.output_file is not None
        if format == "pptx":
            subprocess.call(["open", ctx.output_file])
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
@click.option("-v", "--verbose", count=True)
def rerun(input_file: Path, out: Path, formats: list[str], verbose: int = 0):
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
        if format == "pptx":
            subprocess.call(["open", ctx.output_file])
        print(f"Generated file {ctx.output_file}")
