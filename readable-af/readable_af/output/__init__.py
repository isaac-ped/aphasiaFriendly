
from pathlib import Path
from typing import Protocol


class Generator(Protocol):
    @staticmethod
    def generate(summary, out: Path):
        ...

def get_generator(format: str) -> Generator:
    from . import pptx, yaml

    if format == "pptx":
        return pptx.PPTXGenerator()
    if format == "yaml":
        return yaml.YamlGenerator()
    raise ValueError(f"Unknown format {format}")