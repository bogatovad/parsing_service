from datetime import datetime
import requests
import logging


# Настройка логгирования
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("kudago_gateway.log"),
        logging.StreamHandler()
    ]
)

class KudaGoGateway:
    BASE_URL = "https://kudago.com/public-api/v1.4"
    DATE_FORMAT = "%Y-%m-%d"
    DATETIME_FORMAT = "%d.%m.%Y %H:%M"

    SECONDS_DAY = 86400
    TIME_NOW = int(datetime.now().timestamp())
    TIME_START = TIME_NOW - SECONDS_DAY * 2  # -2 дня
    TIME_END = TIME_START + SECONDS_DAY * 90  # +3 месяца

    def __init__(self, client=None) -> None:
        """
        Инициализирует объект KudaGoGateway с клиентом.
        """
        self.client = client
        logging.info("Инициализирован KudaGoGateway")


    def _fetch_event_details(self, event_id: int) -> dict | None:
        """
        Получает детали события по его ID.
        """
        event_url = f"{self.BASE_URL}/events/{event_id}?expand=place,location,dates&text_format=text"
        try:
            response = requests.get(event_url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Ошибка при запросе деталей события {event_id}: {e}")
            return None


    def _parse_event(self, event: dict) -> dict:
        """
        Парсит событие и возвращает его в формате, удобном для использования.
        """
        id = event['id']

        event = self._fetch_event_details(event["id"])
        event['place'] = "" if not 'place' in event.keys() else event['place']

        current_event = {
            "id": event.get("id", "-"),
            "title": event.get("title", "-"),
            "description": event.get("description", "-"),
            "tags": event.get("tags", []),
            "address": self._get_event_address(event),
            "contact": event.get("place", {}).get("phone", "-") if event['place'] is not None else "-",
            "datestart": self._get_event_start_date(event),
            "dateend": event.get("dates", [{}])[0].get("end_date", ""),
            "cost": event.get("price", ""),
            "url": "",
            "image": "",
        }

        if event:
            current_event.update(self._parse_event_details(event))

        return current_event


    def _parse_event_details(self, event_details: dict) -> dict:
        """
        Парсит детали события.
        """
        parsed_details = {
            "url": event_details.get("site_url", ""),
            "image": self._get_event_image(event_details),
            "datestart": self._get_event_start_date_from_details(event_details),
        }

        if not parsed_details["datestart"]:
            parsed_details["datestart"] = "В рабочие часы"

        return parsed_details


    def _get_event_address(self, event: dict) -> str:
        """
        Возвращает адрес события.
        """
        place = event.get("place", {})

        if place is None:
            #если не получилось достать, делаем длинную версию
            place = event.get("body_text").split('\n')[-1].strip().replace('KudaGo: ', '')
        else:
            place = f"{place.get('title', '')}\n{place.get('address', '')}".strip()

        return place


    def _get_event_start_date(self, event: dict) -> str:
        """
        Возвращает дату начала события.
        """
        start_date = event.get("dates", [{}])[0].get("start", 0)
        return datetime.today().strftime(self.DATE_FORMAT) \
        if (self.TIME_NOW - self.SECONDS_DAY) > start_date \
        else event["dates"][0].get("start_date", "")


    def _get_event_start_date_from_details(self, event_details: dict) -> str:
        """
        Возвращает дату начала события из деталей.
        """
        dates = event_details.get("dates", [])
        if dates and not dates[-1].get("is_startless", True):
            return datetime.fromtimestamp(dates[-1]["start"]).strftime(self.DATETIME_FORMAT)
        return ""


    def _get_event_image(self, event_details: dict) -> bytes:
        """
        Возвращает изображение события.
        """
        image_link = event_details.get("images", [{}])[0].get("image", "")
        if image_link:
            try:
                response = requests.get(image_link)
                response.raise_for_status()
                return response.content
            except requests.RequestException as e:
                logging.error(f"Ошибка при загрузке изображения: {e}")
        return b""


    def _add_kuda_go_events(self, current_json: list[dict]) -> list[dict]:
        """
        Добавляет события из JSON в список.
        """
        events_list = []
        for event in current_json:
            #еще одно условие, чтобы акций не было
            passed_condition = False
            if 'categories' in event.keys():
                passed_condition = False
                if not 'stock' in event['categories']:
                    passed_condition = True
            else:
                passed_condition = True

                if passed_condition:
                    try:
                        parsed_event = self._parse_event(event)
                        if "акции и скидки" not in parsed_event["tags"]:
                            events_list.append(parsed_event)
                    except Exception as e:
                        logging.error(f"Ошибка при добавлении события {event['id']}: {e}")
                        input(f'{e}')
        return events_list


    def fetch_content(self) -> list[dict]:
        """
        Получает события с KudaGo.
        """

        events = []
        for free in [0, 1]:
            passed = True
            page = 0
            while passed:
                page+=1
                url = f"{self.BASE_URL}/events/?lang=ru&page={page}&page_size=100&fields=" + \
                "id,title,dates,tags,price,place,description,price&expand=images,place,location,dates" + \
                f"&text_format=text&location=nnv&actual_since={self.TIME_START}&actual_until={self.TIME_END}&is_free={free}"
                try:
                    response = requests.get(url)
                    if response.status_code == 200:
                        passed = True
                    else:
                        passed = False
                        continue

                    response.raise_for_status()

                    result_json = response.json()["results"]
                    events.extend(self._add_kuda_go_events(result_json))
                except requests.RequestException as e:
                    logging.error(f"Ошибка при запросе событий: {e}")
                    break

        return events

if __name__ == "__main__":
    gateway = KudaGoGateway()
    try:
        events = gateway.fetch_content()
        logging.info(f"Успешно получено {len(events)} событий")
    except Exception as e:
        logging.critical(f"Критическая ошибка при получении событий: {e}")
