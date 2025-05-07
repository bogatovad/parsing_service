import requests
import logging
import re
import time
from datetime import datetime
from interface_adapters.gateways.parsing_base_gateway.base_gateway import BaseGateway

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)


class KudaGoAPIClient:
    BASE_URL = "https://kudago.com/public-api/v1.4"

    def get_events(self, location, start, end, free, page):
        url = (
            f"{self.BASE_URL}/events/?lang=ru&page={page}&page_size=100&fields=id,title,dates,"
            f"tags,price,place,description,price&expand=images,place,location,dates&text_format=text&"
            f"location={location}&actual_since={start}&actual_until={end}&is_free={free}"
        )
        return self._safe_request(url)

    def get_event_details(self, event_id):
        url = f"{self.BASE_URL}/events/{event_id}?expand=place,location,dates&text_format=text"
        return self._safe_request(url)

    def get_place_timetable(self, place_id):
        url = f"{self.BASE_URL}/places/{place_id}"
        return self._safe_request(url)

    def _safe_request(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Request error: {e}")
            return {}


class ImageDownloader:
    @staticmethod
    def download(url):
        if not url:
            return b""
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logging.error(f"Image download error: {e}")
            return b""


class EventParser:
    DATE_FORMAT = "%Y-%m-%d"
    DATETIME_FORMAT = "%d.%m.%Y %H:%M"
    WEEKDAYS = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]

    def __init__(self, image_downloader: ImageDownloader, api_client: KudaGoAPIClient):
        self.image_downloader = image_downloader
        self.api_client = api_client

    def parse_event(self, event):
        details = self.api_client.get_event_details(event["id"])

        result = {
            "id": details.get("id", "-"),
            "name": self._capitalize(details.get("title", "-")),
            "description": self._clean_text(details.get("description", "")),
            "tags": details.get("tags", []),
            "location": self._parse_address(details),
            "contact": details.get("place", {}).get("phone", "-"),
            "date_start": self._get_event_start_date(details),
            "date_end": details.get("dates", [{}])[-1].get("end_date", ""),
            "cost": min(self._parse_price(details.get("price"))),
            "url": details.get("site_url", ""),
            "image": self.image_downloader.download(self._get_image_url(details)),
            "city": "nn",
            "time": self._parse_schedule(details),
            "is_endless": details.get("dates", [{}])[-1].get("is_endless", False),
        }

        return result

    def _parse_price(self, price_text):
        if not price_text:
            return [0]
        numbers = re.findall(r"\d+", price_text)
        return [int(n) for n in numbers] if numbers else [0]

    def _clean_text(self, text):
        return re.sub(r"[^\w\s]", "", text or "").strip()

    def _capitalize(self, text):
        return text.capitalize() if text else "-"

    def _parse_address(self, event):
        place = event.get("place") or {}
        title = place.get("title", "")
        address = place.get("address", "")
        return self._clean_text(f"{title} {address}".strip()) or "-"

    def _get_event_start_date(self, event):
        dates = event.get("dates", [])
        if not dates:
            return ""
        start = dates[-1].get("start", 0)
        now = int(time.time()) - 86400
        return (
            datetime.today().strftime(self.DATE_FORMAT)
            if start < now
            else dates[-1].get("start_date", "")
        )

    def _get_image_url(self, event):
        images = event.get("images", [])
        return images[0].get("image") if images else ""

    def _parse_schedule(self, event_details):
        dates = event_details.get("dates", [])
        result = []

        for date in dates:
            schedules = date.get("schedules", [])
            if schedules:
                for sch in schedules:
                    days = ", ".join(
                        [self.WEEKDAYS[d] for d in sch.get("days_of_week", [])]
                    )
                    start = sch.get("start_time", "00:00:00")[:5]
                    end = sch.get("end_time")
                    time_range = f"{start}-{end[:5]}" if end else f"с {start}"
                    result.append(f"{days}: {time_range}".lower())
            else:
                start_date = date.get("start_date") or datetime.now().strftime(
                    self.DATE_FORMAT
                )
                result.append(
                    f"{start_date} с {date.get('start_time', '00:00:00')[:5]}".lower()
                )

        return "".join(result) if result else "Подробности в описании"


class KudaGoGateway(BaseGateway):
    SECONDS_DAY = 86400
    TIME_NOW = int(time.time())
    TIME_START = TIME_NOW - SECONDS_DAY * 2
    TIME_END = TIME_START + SECONDS_DAY * 90

    def __init__(self, client=None):
        self.client = KudaGoAPIClient()
        self.parser = EventParser(ImageDownloader(), self.client)

    def fetch_content(self):
        events = []
        for is_free in [0, 1]:
            page = 1
            while True:
                page_data = self.client.get_events(
                    "nnv", self.TIME_START, self.TIME_END, is_free, page
                )
                page_events = page_data.get("results", [])

                if not page_events:
                    break

                for event in page_events:
                    if "stock" in event.get("categories", []):
                        continue
                    try:
                        parsed = self.parser.parse_event(event)
                        if "акции и скидки" not in parsed["tags"]:
                            events.append(parsed)
                    except Exception as e:
                        logging.error(f"Parse error {event.get('id')}: {e}")

                page += 1
        return events
