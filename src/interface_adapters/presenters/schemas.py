from typing import List, Dict
from pydantic import BaseModel
from datetime import datetime


class ImagePydanticSchema(BaseModel):
    filename: str


class ContentPydanticSchema(BaseModel):
    name: str
    description: str
    tags: List[str]
    image: bytes
    contact: Dict[str, str]
    date_start: datetime
    date_end: datetime | None
    time: str
    location: str
    cost: int
    city: str

    def __repr__(self):
        return f"ContentPydanticSchema(name={self.name}, description={self.description}, tags={self.tags}, " \
               f"cost={self.cost}, date_start={self.date_start}, date_end={self.date_end}, time={self.time}, " \
               f"loc={self.location}, contact={self.contact}"
