import dataclasses
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, NewType, TypeGuard, TypeVar


class UnpopulatedException(Exception):
    """Raised when an icon is not populated but is accessed"""

    pass


class Icon:
    def __init__(self, keyword: str):
        self.keyword = keyword

        self._url: str | None = None
        self._icon: bytes | None = None
        self._id: int | None = None
        self._checksum: int | None = None

    # Use properties to ensure setting the icon also sets the checksum
    @property
    def icon_url(self) -> str:
        if not self.up_to_date(self._url):
            raise UnpopulatedException("Icon not populated")
        return self._url

    @property
    def icon(self) -> bytes:
        if not self.up_to_date(self._icon):
            raise UnpopulatedException("Icon not populated")
        return self._icon

    @property
    def id(self) -> int:
        if not self.up_to_date(self._id):
            raise UnpopulatedException("Icon not populated")
        return self._id

    def __repr__(self):
        return f"Icon<{self.keyword}:{self.id}>"

    def populate(self, icon_url: str, icon: bytes, id: int):
        self._url = icon_url
        self._icon = icon
        self._id = id
        self._checksum = hash((self.keyword, self._id))

    UNSET = object()

    T = TypeVar("T")

    def up_to_date(self, field: T | object = UNSET) -> TypeGuard[T]:
        """Check if the icon is up to date.

        :param field: (optional) A specific field to verify as non-null
        ÷"""
        if field is Icon.UNSET and self._icon is None:
            return False
        elif field is None:
            return False
        return self._checksum == hash((self.keyword, self._id))  # type: ignore

    @property
    def filename(self) -> str:
        """The filename to save the icon to"""
        return f"{self.keyword.replace(' ', '')}-{self.id}.png"

    def write(self, out_dir: Path):
        """Save the icon to the filesystem"""
        icon_path = out_dir / self.filename
        icon_path.write_bytes(self.icon)

    def asdict(self) -> dict[str, Any]:
        return {
            "keyword": self.keyword,
            "_url": self._url,
            "_checksum": self._checksum,
            "_id": self._id,
        }

    @classmethod
    def fromdict(cls, input: dict[str, Any]):
        self = cls(
            keyword=input["keyword"],
        )
        self._url = input["_url"]
        self._checksum = input["_checksum"]
        self._id = input["_id"]
        return self


@dataclass
class Metadata:
    title: str
    authors: list[str]
    date: str

    def asdict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

    @classmethod
    def fromdict(cls, input: dict[str, Any]):
        return cls(**input)


@dataclass
class Bullet:
    text: str
    icons: list[Icon] = field(default_factory=list)

    def asdict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "icons": [icon.asdict() for icon in self.icons],
        }

    @classmethod
    def fromdict(cls, input: dict[str, Any]):
        return cls(
            text=input["text"],
            icons=[Icon.fromdict(icon) for icon in input["icons"]],
        )


@dataclass
class Summary:
    metadata: Metadata
    bullets: list[Bullet]

    def asdict(self) -> dict[str, Any]:
        return {
            "metadata": self.metadata.asdict(),
            "bullets": [bullet.asdict() for bullet in self.bullets],
        }
