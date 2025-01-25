from dataclasses import dataclass
from datetime import datetime


@dataclass
class ContentDto:
    name: str
    description: str
    tags: list[str]
    image: bytes
    contact: dict[str, str]
    date_start: datetime
    date_end: datetime
    time: str
    location: str
    cost: int

    def __repr__(self):
        return (
            f"ContentDataClass(name={self.name!r}, description={self.description!r}, "
            f"tags={self.tags!r}, cost={self.cost!r})"
        )
