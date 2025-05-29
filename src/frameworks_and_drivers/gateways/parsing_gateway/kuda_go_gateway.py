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
            if not '404' in str(e):
                logging.error(f"Request error: {e}")
            else:
                pass
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
    BASE_URL = "https://kudago.com/public-api/v1.4"
    DATE_FORMAT = "%Y-%m-%d"
    DATETIME_FORMAT = "%d.%m.%Y %H:%M"
    WEEKDAYS = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]

    def __init__(self, image_downloader: ImageDownloader, api_client: KudaGoAPIClient):
        self.image_downloader = image_downloader
        self.api_client = api_client

    def parse_event(self, event):
        details = self.api_client.get_event_details(event["id"])
        #details = self.api_client.get_event_details(209952)
        #получить место
        if details['place'] == None:
            text = details.get('body_text')
            pattern = r'Улица.*?\.'

            matches = re.findall(pattern, text)

            details['place'] = {'title' : ' ', 'address' : matches[0], 'phone' : '-'} if len(matches) > 0 \
                else {'title' : ' ', 'address' : 'Уточняйте у организаторов', 'phone' : '-'}

        #if details.get("id") == 217464:
        #    input(details)

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
        }

        return result

    def _parse_price(self, price_text):
        if not price_text:
            return [0]
        numbers = re.findall(r"\d+", price_text)
        if 'бесплатно' in price_text:
            return [0]
        numbers = [int(num) for num in numbers if int(num) > 10]
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

    def _parse_schedule(self, event_details: dict):
        week_day = {0: "пн", 1: "вт", 2: "ср", 3: "чт", 4: "пт", 5: "сб", 6: "вс"}

        def format_time(time_str):
            return ':'.join(time_str.split(':')[:2]) if time_str else None

        def get_days_range(days, week_map):
            if not days:
                return ""
            ranges = []
            days = sorted(days)
            start = end = days[0]

            for day in days[1:]:
                if day == end + 1:
                    end = day
                else:
                    ranges.append((start, end))
                    start = end = day
            ranges.append((start, end))

            return ', '.join([
                f"{week_map[s]}–{week_map[e]}" if s != e else week_map[s]
                for s, e in ranges
            ])

        def create_schedule_entry(days_str, start, end):
            start_time = format_time(start)
            end_time = format_time(end)

            if not start_time:
                return None

            time_part = f"{start_time}–{end_time}" if end_time else f"с {start_time}"
            return f"{days_str}: {time_part}".lower()

        # Основная обработка расписания
        timetable = []
        current_time = time.time()
        use_place_schedule = False

        # Проверяем наличие use_place_schedule=True в dates
        for date in event_details.get('dates', []):
            if date.get('use_place_schedule', False):
                use_place_schedule = True
                break

        # Если нужно использовать расписание места
        if use_place_schedule:
            place = event_details.get('place')
            if place and place.get('id'):
                try:
                    response = requests.get(f"{self.BASE_URL}/places/{place['id']}")
                    if response.status_code == 200:
                        return response.json().get('timetable', '')
                except requests.RequestException:
                    pass  # Продолжаем обработку обычного расписания

        # Обработка обычного расписания
        for date in event_details.get('dates', []):
            if not date.get('is_endless') and date.get('end', 0) < current_time:
                continue

            if date.get('schedules'):
                for schedule in date['schedules']:
                    days_str = get_days_range(schedule.get('days_of_week', []), week_day)
                    entry = create_schedule_entry(
                        days_str,
                        schedule.get('start_time'),
                        schedule.get('end_time')
                    )
                    if entry:
                        timetable.append(entry)

            elif date.get('start_date'):
                try:
                    date_obj = datetime.strptime(date['start_date'], "%Y-%m-%d")
                    date_str = date_obj.strftime("%d.%m")
                except (ValueError, KeyError):
                    date_str = ""

                time_str = ""
                if date.get('start_time'):
                    time_str = format_time(date['start_time'])
                    if date.get('end_time'):
                        time_str += f"–{format_time(date['end_time'])}"
                    else:
                        time_str = f"с {time_str}"

                if date_str and time_str:
                    timetable.append(f"{date_str} {time_str}")

        # Резервное извлечение из body_text
        body_text = event_details.get('body_text', '')
        if 'Стоимость' in body_text:
            matches = re.findall(
                r'!Время:([^\n]+)\nСтоимость:([^\n]+)',
                body_text
            )
            if matches:
                backup_schedule = [
                    f"{t.strip()} (Стоимость: {p.strip()})"
                    for t, p in matches
                ]
                timetable = backup_schedule

        # Форматирование окончательного результата
        if not timetable:
            if 'Улица' in body_text:
                return "Уточняйте расписание"
            return "Уточняйте расписание"

        return '\n'.join(timetable)



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