from interface_adapters.gateways.parsing_base_gateway.base_gateway import BaseGateway
import requests
import time
import re
from datetime import datetime
import logging

# Настройка логгирования
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("kudago_gateway.log"), logging.StreamHandler()],
)


class KudaGoGateway(BaseGateway):
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

        :param client: Клиент, используемый для выполнения запросов (например, bot или API клиент).
        """
        logging.info("KudaGoGateway инициализирован")
        self.client = client

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
        event = self._fetch_event_details(event["id"])
        event["place"] = "" if "place" not in event.keys() else event["place"]

        if event["price"]:
            if "детям" not in event["price"]:
                if re.search("[0-9]{1,10}", event["price"]):
                    prices = re.findall(r"-?\d+(?:\.\d+)?", event["price"])
                    if len(prices) == 2:
                        event["price"] = [
                            int(el)
                            for el in re.findall(r"-?\d+(?:\.\d+)?", event["price"])
                        ]
                    else:
                        event["price"] = [prices[0]]
                else:
                    event["price"] = [0]
            else:
                event["price"] = [
                    0,
                    int(re.findall(r"-?\d+(?:\.\d+)?", event["price"])[0]),
                ]
        else:
            event["price"] = [0]

        # обработка описания
        event["description"] = re.sub(r"[^\w\s]", "", event["description"])

        # Первая буква имени - заглавная
        event["title"] = f"{event['title'][0].upper()}{event['title'][1:]}"
        # input(event['price'])

        current_event = {
            "id": event.get("id", "-"),
            "name": event.get("title", "-"),
            "description": event.get("description", "-"),
            "tags": event.get("tags", []),
            "location": self._get_event_address(event),
            "contact": event.get("place", {}).get("phone", "-")
            if event["place"] is not None
            else "-",
            "date_start": self._get_event_start_date(event),
            "date_end": event.get("dates", [{}])[-1].get("end_date", ""),
            "cost": min(event["price"])
            if event["price"] is not None
            else 0,  # дублируется возможно
            "url": "",
            "image": "",
            "city": "nn",
            "time" : "",
            "is_endless" : event.get('dates', [{'is_endless' : False}])[-1]['is_endless']
            "time": "",
        }

        if event:
            current_event.update(self._parse_event_details(event))
            current_event.update(self._parse_time(event))

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
            # если не получилось достать, делаем длинную версию
            place = (
                event.get("body_text")
                .split("\n")[-1]
                .strip()
                .replace("KudaGo: ", "")
                .replace("Фото: предоставлено организатором", "")
            )
        else:
            place = f"{place.get('title', '')}\n{place.get('address', '')}".strip()

        # доп.очистка
        place = re.sub(r"[^\w\s]", "", place).strip()
        return place

    def _get_event_start_date(self, event: dict) -> str:
        """
        Возвращает дату начала события.
        """
        start_date = event.get("dates", [{}])[-1].get("start", 0)
        return (
            datetime.today().strftime(self.DATE_FORMAT)
            if (self.TIME_NOW - self.SECONDS_DAY) > start_date
            else event["dates"][-1].get("start_date", "")
        )

    def _get_event_start_date_from_details(self, event_details: dict) -> str:
        """
        Возвращает дату начала события из деталей.
        """
        dates = event_details.get("dates", [])
        if dates and not dates[-1].get("is_startless", True):
            return datetime.fromtimestamp(dates[-1]["start"]).strftime(
                self.DATETIME_FORMAT
            )
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

    def _parse_time(self, event_details : dict):

        week_day = {0 : "Пн", 1 : "Вт", 2 : "Ср", 3 : "Чт", 4 : "Пт", 5 : "Сб", 6 : "Вс"}
        timetable, schedule_list, schedule_t_string   = '', [], ''
        if event_details['id'] == '200189':
            input(len(event_details['dates']))
        if len(event_details['dates']) == 1:

            use_schedule = event_details['dates'][0]['use_place_schedule']
            event_date = event_details['dates'][0]

            start_date_none = event_date["start_date"] is None
            end_date_none = event_date["end_date"] is None
            end_time_none = (event_date["end_time"] is None or event_date["end_time"] == "00:00:00")

            start_time_midnight = True if (event_date.get('start_time') == '00:00:00' or event_date.get('start_time') is None) else False

            none_condition = True if (start_date_none and end_date_none) or (start_date_none and start_time_midnight and end_time_none) else False

            if use_schedule == False and none_condition == True and event_date['schedules'] == []:
                #специальный случай, когда из апишных непонятно, когда у нас начало и конец. обычно такая инфа дается в описании
                schedule_t_string = 'Подробности в описании'

            elif use_schedule is True:
                place_id = event_details["place"].get("id")
                place_data = requests.get(f"{self.BASE_URL}/places/{place_id}")
                timetable = place_data.json()['timetable']

            elif not start_date_none and not start_time_midnight:
                element_append = f"{event_date['start_time'].split(':')[0]}:{event_date['start_time'].split(':')[1]}"
                schedule_list.append(element_append)

            elif event_details['dates'][0]['schedules'] != []:
                schedules = event_details['dates'][0]['schedules']
                schedule_list, schedule_string = [], ''

                #inter_string = ''
                for n, schedule in enumerate(schedules):
                    days = schedule['days_of_week']
                    inter_string = ''

                    if len(days) > 1:
                        for d, day in enumerate(schedule['days_of_week']):
                            for day in days:
                                first = days[0]
                                status = False if len(days) == 1 else True
                                if not status:
                                    break
                                still_continue = True
                                if status and d < len(days)-1:
                                    still_continue = True if days[d] + 1 == days[d+1] else False
                                    last = days[d+1]
                                    # врзможно стоит дополнить случваем, когда у нас still_continue false, но элементы еще есть
                                    if not still_continue:
                                        inter_string = f"{week_day[first]} - {week_day[last]}"
                                elif day == days[len(days)-1] and still_continue:
                                    last = day
                                    if not inter_string:
                                        inter_string = f"{week_day[first]} - {week_day[last]}"
                                    break

                    if len(days) == 1:
                        inter_string = f'{week_day[days[0]]}'
                    days_of_week = inter_string if inter_string else ', '.join([week_day[el] for el in schedule['days_of_week']])
                    #Специальный случай (в ходе тестирования end_time по событиям null)
                    end_time = True if schedule['end_time'] is not None else False

                    #    schedule['end_time'] = "18:00:00"
                    try:
                        if end_time:
                            schedule_t_string = f"{days_of_week}: {schedule['start_time'].split(':')[0]}:{schedule['start_time'].split(':')[1]}-{schedule['end_time'].split(':')[0]}:{schedule['end_time'].split(':')[1]}"
                        else:
                            schedule_t_string = f"{days_of_week}: c {schedule['start_time'].split(':')[0]}:{schedule['start_time'].split(':')[1]}"
                    except AttributeError:
                        schedule_t_string = "Уточняйте у организаторов"

                    schedule_list.append(schedule_t_string.lower())
            else:
                start_date_none = event_date["start_date"] is None
                end_date_none = event_date["end_date"] is None
                start_time_midnight = event_date.get("start_time") == "00:00:00"

                none_condition = True if (start_date_none and end_date_none) or (start_date_none and start_time_midnight) else False

                if not (start_date_none and end_date_none) or not (start_date_none and start_time_midnight) :
                    format_date = f'{event_date["start_date"].split("-")[2]}.{event_date["start_date"].split("-")[1]}'
                    end_time = True if event_date["end_time"] is not None else False
                    schedule_t_string = ""
                    try:
                        if end_time:
                            time_start_end = f'{":".join(event_date["start_time"].split(":")[:2])}-{":".join(event_date["end_time"].split(":")[:2])}'
                        else:
                            time_start_end = (
                                f'с {":".join(event_date["start_time"].split(":")[:2])}'
                            )
                    except AttributeError:
                        schedule_t_string = "Уточняйте у организаторов"
                    schedule_t_string = (
                        f"{format_date} {time_start_end}"
                        if not schedule_t_string
                        else schedule_t_string
                    )
                else:
                    schedule_t_string = "Подробности в описании"

                schedule_list.append(schedule_t_string.lower())

            schedule_string = '\n'.join(schedule_list)
            timetable = schedule_string if schedule_string else timetable

        else:
            try:
                schedule_string, schedule_list, end_time = '', [], False
                for date in event_details['dates']:
                    if date['schedules'] != [] and date['is_endless'] == True:
                        schedules = date['schedules']
                        for n, schedule in enumerate(schedules):
                            days_of_week = ', '.join([week_day[el] for el in schedule['days_of_week']])
                            end_time = True if schedule["end_time"] is not None else False
                            if end_time:
                                schedule_t_string = f"{days_of_week}: {schedule['start_time'].split(':')[0]}:{schedule['start_time'].split(':')[1]}-{schedule['end_time'].split(':')[0]}:{schedule['end_time'].split(':')[1]}"
                            else:
                                schedule_t_string = f"{days_of_week}: c {schedule['start_time'].split(':')[0]}:{schedule['start_time'].split(':')[1]}"

                            if schedule_list != []:
                                # что если уже присутствует в днях недели
                                already_present = True if True in [True for day in week_day.values() if
                                                                   day in schedule_t_string] else False

                                if schedule_t_string not in schedule_list and not already_present:
                                    schedule_list.append(schedule_t_string)
                                elif schedule_t_string not in schedule_list and already_present:
                                    what_presents = schedule_t_string.split(': ')[0]
                                    current_substring = [el.split(': ') for el in schedule_list if what_presents in el][0][1]
                                    index_position = [True for el in schedule_list if what_presents in el].index(True)
                                    to_append = schedule_t_string.split(': ')[1]
                                    print(to_append)
                                    schedule_list[index_position] = f'{what_presents}: {current_substring}, {to_append}'
                            else:
                                schedule_list.append(schedule_t_string.lower())

                    elif date['end'] > round(time.time(),0):
                        if date['schedules'] != []:
                          
                            # повторение из прошлого
                            schedules = event_details["dates"][0]["schedules"]
                            schedule_list, schedule_string = [], ""
                            for n, schedule in enumerate(schedules):
                                days_of_week = ", ".join(
                                    [week_day[el] for el in schedule["days_of_week"]]
                                )
                                end_time = (
                                    True if date["end_time"] is not None else False
                                )
                                if end_time:
                                    schedule_t_string = f"{days_of_week}: {schedule['start_time'].split(':')[0]}:{schedule['start_time'].split(':')[1]}-{schedule['end_time'].split(':')[0]}:{schedule['end_time'].split(':')[1]}"
                                else:
                                    schedule_t_string = f"{days_of_week}: c {schedule['start_time'].split(':')[0]}:{schedule['start_time'].split(':')[1]}"
                        else:
                            start_date = (
                                date["start_date"]
                                if date["start_date"] is not None
                                else datetime.today().strftime("%Y-%m-%d")
                            )
                            date_format = (
                                f'{start_date.split("-")[2]}.{start_date.split("-")[1]}'
                            )
                            end_time = True if date["end_time"] is not None else False
                            if end_time:
                                schedule_t_string = f'{date_format} {":".join(date["start_time"].split(":")[:2])}-{":".join(date["end_time"].split(":")[:2])}'
                            else:
                                schedule_t_string = f'{date_format} с {":".join(date["start_time"].split(":")[:2])}'

                        # убираем дубликаты
                        schedule_list.append(schedule_t_string.lower())

                if len(schedule_list) == 1 and not event_details['dates'][0]['is_endless']:
                    print(event_details['id'])
                    schedule_list[0] = schedule_list[0].split(' с ')[1] \
                        if ' с ' in schedule_list[0] \
                        else schedule_list[0].split(' ')[1]


                schedule_string = '\n'.join(schedule_list)
                timetable = schedule_string
            except Exception as e:
                input(f'Ошибка в _parse_time : {e} : {event_details}')

        return {"time" : timetable}

    def _add_kuda_go_events(self, current_json: list[dict]) -> list[dict]:
        """
        Добавляет события из JSON в список.
        """
        events_list = []
        for event in current_json:
            # еще одно условие, чтобы акций не было
            passed_condition = False
            if "categories" in event.keys():
                passed_condition = False
                if "stock" not in event["categories"]:
                    passed_condition = True
            else:
                passed_condition = True
            if passed_condition:
                try:
                    parsed_event = self._parse_event(event)
                    if "акции и скидки" not in parsed_event["tags"]:
                        events_list.append(parsed_event)
                except KeyError:
                    # бывает неправильно парсится (1 событие в выборке)
                    continue
                except Exception as e:
                    logging.error(f"Ошибка при добавлении события {event['id']}: {e}")
                    input(f"{e}")
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
                page += 1
                url = (
                    f"{self.BASE_URL}/events/?lang=ru&page={page}&page_size=100&fields=id,title,dates,"
                    f"tags,price,place,description,price&expand=images,place,location,dates&text_format=text&"
                    f"location=nnv&actual_since={self.TIME_START}&actual_until={self.TIME_END}&is_free={free}"
                )
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
