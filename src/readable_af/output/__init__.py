from . import pptx, yaml, html, gdocs, comparison, generator

def get_generator(format: str) -> generator.Generator:

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
