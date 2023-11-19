from dataclasses import dataclass, field
from pathlib import Path
from ..config import Config


@dataclass
class Icon:
    keyword: str
    icon_url: str
    icon: bytes
    id: int  # A unique ID to identify this icon so the same icon isn't used more than once

    @property
    def filename(self) -> str:
        """The filename to save the icon to"""
        return f"{self.keyword}.png"

    def save(self, out_dir: Path):
        """Save the icon to the filesystem"""
        icon_path = out_dir / self.filename
        icon_path.write_bytes(self.icon)


@dataclass
class Metadata:
    title: str
    authors: list[str]
    date: str


@dataclass
class Bullet:
    text: str
    icons: list[Icon] = field(default_factory=list)


@dataclass
class Summary:
    metadata: Metadata
    bullets: list[Bullet]
