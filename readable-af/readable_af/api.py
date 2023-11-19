"""High level API for readable-AF"""

from pathlib import Path
from .model.request import Ctx
from .processing import summarization
from .output import pptx

DEFAULT_OUT_DIR = Path("./output/")


def summarize(ctx: Ctx):
    """Summarize a document to pptx"""
    assert ctx.input.file is not None
    summary = summarization.summarize(ctx.input.file)
    if ctx.output_file is None:
        ctx.output_file = DEFAULT_OUT_DIR / ctx.input.file.stem / "summary.pptx"
    pptx.generate(summary, ctx.output_file)
