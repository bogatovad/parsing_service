from typing import List
from pydantic import BaseModel
from datetime import datetime
import base64

class ImagePydanticSchema(BaseModel):
    filename: str

class ContentPydanticSchema(BaseModel):
    name: str
    description: str
    tags: List[str]
    image: bytes
    contact: List[str]                # Изменили тип с Dict[str, str] на List[str]
    date_start: datetime
    date_end: datetime | None
    time: str
    location: str
    cost: int
    city: str

    def __repr__(self):
        return (
            f"ContentPydanticSchema(name={self.name}, description={self.description}, tags={self.tags}, "
            f"cost={self.cost}, date_start={self.date_start}, date_end={self.date_end}, time={self.time}, "
            f"location={self.location}, contact={self.contact}, links={self.links})"
        )

    class Config:
        json_encoders = {
            # Кодирует байтовые данные в base64, если они есть, иначе возвращает пустую строку.
            bytes: lambda v: base64.b64encode(v).decode('utf-8') if v else ""
        }
