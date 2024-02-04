"""High level API for readable-AF"""

from pathlib import Path

from .model.request import Ctx
from .output import get_generator
from .processing import summarization

DEFAULT_OUT_DIR = Path("./outputs/")
RERUN_OUT_DIR = Path("./outputs/rerun/")


def summarize(ctx: Ctx):
    """Summarize a document to pptx"""
    input = ctx.input
    assert input.abstract is not None or input.file is not None
    summary = summarization.summarize(ctx)
    if ctx.output_file is None:
        assert ctx.input.file is not None
        ctx.output_file = (
            DEFAULT_OUT_DIR / ctx.input.file.stem / f"summary.{ctx.output_format}"
        )
    generator = get_generator(ctx.output_format)
    generator.generate(summary, ctx.output_file)


def rerun(ctx: Ctx):
    """Re-run the summary generation process on a previously summarized file."""
    assert ctx.input.file is not None
    summary = summarization.reload(ctx.input.file)
    if ctx.output_file is None:
        if ctx.input.file.stem != "summary":
            stem = ctx.input.file.parent.name
        else:
            stem = ctx.input.file.stem
        ctx.output_file = RERUN_OUT_DIR / stem / f"summary.{ctx.output_format}"
    generator = get_generator(ctx.output_format)
    generator.generate(summary, ctx.output_file)
