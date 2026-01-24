
from enum import Enum
from pydantic import BaseModel, Field

class IconSource(Enum):
  NOUNPROJECT = "nounproject"

class SearchResult(BaseModel):
  source: IconSource = IconSource.NOUNPROJECT
  id: str = Field(description="ID for the icon on nounproject")
  tags: list[str] = Field(description="A list of tags associated with this icon")
  collection_names: list[str] = Field(description="A list of the collections this icon belongs to")
