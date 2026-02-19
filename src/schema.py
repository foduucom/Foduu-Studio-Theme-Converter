from pydantic import BaseModel
from typing import List, Any

class ShortcodeSchema(BaseModel):
    name: str
    param: List[Any]
    template: str
    queryScript: str


class ReadmeMetadata(BaseModel):
    description: str
    tags: List[str]