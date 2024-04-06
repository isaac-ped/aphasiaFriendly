from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Any

from .summary import Summary


@dataclass
class Input:
    """User-provided input to a request."""

    file: Path | None = None
    title: str | None = None
    authors: str | None = None
    abstract: str | None = None

@dataclass
class Ctx:
    """Context for a request.

    Fields start as empty and will be filled over the course of the request.
    """

    input: Input = field(default_factory=Input)
    credentials: Any | None = None
    output_format: str = "pptx"
    file_contents: str | None = None
    preamble_contents: str | None = None
    summary: Summary | None = None
    output_dir: Path | None = None
    output_file: Path | None = None
    output_link: str | None = None