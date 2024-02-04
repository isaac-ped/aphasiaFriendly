
from pathlib import Path
from typing import Protocol

from ..model.request import Ctx


class Generator(Protocol):
    @staticmethod
    def generate(summary, ctx: Ctx):
        ...

def get_generator(format: str) -> Generator:
    from . import pptx, yaml, html, gdocs

    if format == "pptx":
        return pptx.PPTXGenerator()
    if format == "yaml":
        return yaml.YamlGenerator()
    if format == "html":
        return html.HtmlGenerator()
    if format == "gdoc":
        return gdocs.GoogleDocGenerator()
    raise ValueError(f"Unknown format {format}")