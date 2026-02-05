from pydantic import BaseModel, Field
from pathlib import Path
from typing import Any, TypeGuard, TypeVar, ClassVar
from ..logger import logger

T = TypeVar("T")


class UnpopulatedException(Exception):
    """Raised when an icon is not populated but is accessed"""

    pass


class Icon(BaseModel):
    keyword: str = Field(
        description="A keyword for the icon, typically 1-3 words that represent the concept"
    )
    _icon: bytes | None = None
    id: int = Field(
        description="The id for this icon on NounProject"
    )

    def calculate_checksum(self) -> int:
        return hash((self.keyword, self.id))#_id))

    @property
    def icon(self) -> bytes:
        if not self.up_to_date(self._icon):
            raise UnpopulatedException("Icon not populated")
        return self._icon

    def __repr__(self):
        return f"Icon<{self.keyword}:{self.id}>"

    def populate(self,  icon: bytes): 
        self._icon = icon

    UNSET: ClassVar[object] = object()

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
            "id": self.id,
            "_checksum": self.calculate_checksum(),
        }

    @classmethod
    def fromdict(cls, input: dict[str, Any]):
        self = cls(
            keyword=input["keyword"],
            id=input["id"],#"_id"],
        )
        if input["_checksum"] != self.calculate_checksum():
            logger.info("Icon checksum mismatch, resetting")
        return self


class Metadata(BaseModel):
    title: str
    authors: list[str]
    date: str
    simplified_title: str = Field(
        description="A short, simple title for the paper that's easier to understand",
    )

    def asdict(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def fromdict(cls, input: dict[str, Any]):
        return cls(**input)


class Bullet(BaseModel):
    text: str = Field(
        description="The bullet point text with HTML <b> tags for important words/phrases"
    )
    icons: list[Icon] = Field(
        default_factory=list,
        description="0-3 icon keywords for this bullet point, ordered from most to least important. Each Icon should have only the keyword field populated.",
    )

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
    metadata: Metadata | None = None
    rating: str = "N/A"
    bullets: list[Bullet] = Field(default_factory=list)

    def asdict(self) -> dict[str, Any]:
        return {
            "metadata": self.metadata.asdict() if self.metadata else None,
            "bullets": [bullet.asdict() for bullet in self.bullets],
        }
