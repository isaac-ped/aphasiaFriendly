from typing import Protocol

from ..model.request import Ctx


class Generator(Protocol):
    @staticmethod
    def generate(summary, ctx: Ctx): ...


def get_generator(format: str) -> Generator:
    from . import pptx, yaml, html, gdocs, comparison

    if format == "pptx":
        return pptx.PPTXGenerator()
    if format == "yaml":
        return yaml.YamlGenerator()
    if format == "html":
        return html.HtmlGenerator()
    if format == "gdoc":
        return gdocs.GoogleDocGenerator()
    if format == "comparison":
        return comparison.ComparisonGenerator()

    raise ValueError(f"Unknown format {format}")
