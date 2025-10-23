from pydantic import BaseModel, Field
from pathlib import Path
from typing import Any, TypeGuard, TypeVar, ClassVar
from ..logger import logger


class UnpopulatedException(Exception):
    """Raised when an icon is not populated but is accessed"""

    pass


class Icon(BaseModel):
    keyword: str
    _url: str | None = None
    _icon: bytes | None = None
    _id: int | None = None

    def calculate_checksum(self) -> int:
        return hash((self.keyword, self._id))

    # Use properties to ensure setting the icon also sets the checksum
    @property
    def url(self) -> str:
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
        return f"Icon<{self.keyword}:{self._id}>"

    def populate(self, icon_url: str, icon: bytes, id: int):
        self._url = icon_url
        self._icon = icon
        self._id = id

    UNSET: ClassVar[object] = object()

    T: ClassVar[TypeVar] = TypeVar("T")

    def up_to_date(self, field: T | object = UNSET) -> TypeGuard[T]:
        """Check if the icon is up to date.

        :param field: (optional) A specific field to verify as non-null
        ÷"""
        if field is Icon.UNSET and self._icon is None:
            return False
        elif field is None:
            return False
        return True

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
            "_id": self._id,
            "_checksum": self.calculate_checksum(),
        }

    @classmethod
    def fromdict(cls, input: dict[str, Any]):
        self = cls(
            keyword=input["keyword"],
            _url=input["_url"],
            _id=input["_id"],
        )
        if input["_checksum"] != self.calculate_checksum():
            logger.info("Icon checksum mismatch, resetting")
            self._url = None
            self._id = None
        return self


class Metadata(BaseModel):
    title: str
    authors: list[str]
    date: str
    simplified_title: str | None = None

    def asdict(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def fromdict(cls, input: dict[str, Any]):
        return cls(**input)


class Bullet(BaseModel):
    text: str
    icons: list[Icon] = Field(default_factory=list)

    def calculate_checksum(self) -> int:
        return hash(self.text)

    def asdict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "icons": [icon.asdict() for icon in self.icons],
        }

    @classmethod
    def fromdict(cls, input: dict[str, Any]) -> "Bullet":
        self = cls(text=input["text"])
        self.icons = [Icon.fromdict(icon) for icon in input["icons"]]
        return self


class Summary(BaseModel):
    metadata: Metadata
    rating: str = "N/A"
    bullets: list[Bullet] = Field(default_factory=list)

    def asdict(self) -> dict[str, Any]:
        return {
            "metadata": self.metadata.asdict(),
            "bullets": [bullet.asdict() for bullet in self.bullets],
        }
