from pathlib import Path
import subprocess
import click
from .logger import setup_logging
from .model.request import Ctx
from . import api


@click.group()
def cli():
    pass


@cli.command()
@click.argument("input_file", type=Path)
@click.option("--out", type=Path, help="output directory", default=None)
@click.option("-v", "--verbose", count=True)
def summarize(input_file: Path, out: Path, verbose: int = 0):
    """Create an aphasia-friendly summary of an academic paper abstract."""
    setup_logging(verbose)

    ctx = Ctx()
    ctx.input.file = input_file
    ctx.output_file = out

    api.summarize(ctx)

    subprocess.call(["open", ctx.output_file])
