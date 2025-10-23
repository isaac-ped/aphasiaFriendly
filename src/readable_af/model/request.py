<<<<<<< Updated upstream
import pydantic.dataclasses
from pydantic.dataclasses import dataclass, field
=======
from pydantic import BaseModel, Field
>>>>>>> Stashed changes
from pathlib import Path
from typing import Any

from .summary import Summary


class Input(BaseModel):
    """User-provided input to a request."""

    file: Path | None = None
    title: str | None = None
    authors: str | None = None
    abstract: str | None = None


class Ctx(BaseModel):
    """Context for a request.

    Fields start as empty and will be filled over the course of the request.
    """

    input: Input = Field(default_factory=Input)
    credentials: Any | None = None
    output_format: str = "pptx"
    file_contents: str | None = None
    preamble_contents: str | None = None
    summary: Summary | None = None
    output_dir: Path | None = None
    output_file: Path | None = None
    output_link: str | None = None
