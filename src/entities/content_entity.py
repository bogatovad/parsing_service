from uuid import UUID, uuid4
from enum import Enum
from typing import List, Dict
from datetime import datetime, time


class ContentType(Enum):
    EVENT = "Event"
    PLACE = "Place"


class ContentEntity:
    def __init__(
        self,
        type: ContentType,
        name: str,
        description: str,
        tags: List[str],
        image: bytes,
        contact: Dict[str, str],
        date_start: datetime,
        date_end: datetime,
        time: time,
        location: str,
        cost: int,
    ):
        self.id: UUID = uuid4()
        self.type: ContentType = type
        self.name: str = name
        self.description: str = description
        self.tags: List[str] = tags
        self.image: bytes = image
        self.contact: Dict[str, str] = contact
        self.date_start: datetime = date_start
        self.date_end: datetime = date_end
        self.time: time = time
        self.location: str = location
        self.cost: int = cost

    def __repr__(self):
        return (
            f"ContentEntity(id={self.id}, type={self.type}, name={self.name}, "
            f"description={self.description}, tags={self.tags}, location={self.location}, "
            f"cost={self.cost}, date_start={self.date_start}, date_end={self.date_end})"
        )