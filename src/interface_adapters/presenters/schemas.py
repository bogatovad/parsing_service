from pydantic import BaseModel
from datetime import datetime
import base64
from typing import Literal


class ImagePydanticSchema(BaseModel):
    filename: str


class ContentPydanticSchema(BaseModel):
    name: str
    description: str
    tags: list[str]
    image: bytes
    contact: list[dict[str, str]]
    date_start: datetime | None
    date_end: datetime | None
    time: str
    location: str
    cost: int
    city: str
    unique_id: str
    event_type: Literal["online", "offline"] = "offline"
    publisher_type: Literal["user", "organisation"] = "user"
    publisher_id: int = 1_000_000

    def __repr__(self):
        return (
            f"ContentPydanticSchema(name={self.name}, description={self.description}, tags={self.tags}, "
            f"cost={self.cost}, date_start={self.date_start}, date_end={self.date_end}, time={self.time}, "
            f"location={self.location}, contact={self.contact}, event_type={self.event_type}, "
            f"publisher_type={self.publisher_type}, publisher_id={self.publisher_id})"
        )

    class Config:
        json_encoders = {
            # Кодирует байтовые данные в base64, если они есть, иначе возвращает пустую строку.
            bytes: lambda v: base64.b64encode(v).decode("utf-8") if v else ""
        }
