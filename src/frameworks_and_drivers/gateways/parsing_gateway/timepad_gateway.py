from typing import List, Dict

from interface_adapters.gateways.parsing_base_gateway.base_gateway import BaseGateway
import requests
from datetime import datetime
import logging


logging.basicConfig(level=logging.INFO)


class TimepadGateway(BaseGateway):
    def __init__(self, client=None) -> None:
        """
        Инициализирует объект Timepad с клиентом.

        :param client: Клиент, используемый для выполнения запросов (например, bot или API клиент).
        """
        self.client = client

    def fetch_content(self) -> List[Dict]:
        """
        Метод для получения событий из Timepad. Должен быть реализован в соответствии с API.

        :events: Список событий в виде словарей.
        """
        events = []

        current_date = datetime.now().date()
        formatted_current_date = current_date.strftime("%Y-%m-%d")
        skip = 0
        limit = 50

        while True:
            params = {
                "fields": "location,image,ticket_types,description_short,organization,ends_at",
                "cities": "Нижний Новгород",
                "starts_at_min": formatted_current_date,
                "sort": "starts_at",
                "skip": skip,
                "limit": limit,
            }
            headers = {
                "Authorization": "Bearer 23ee52ea2569153a9b1abcaa24682020aa2363ba"
            }
            api_url = "https://api.timepad.ru/v1/events"
            logging.info(f"Получаем события с Timepad: {api_url} {params} {headers}")
            response = requests.get(api_url, params=params, headers=headers)
            logging.info(
                f"Получили ответ от Timepad: {response.status_code} {response.text}"
            )
            response.raise_for_status()

            events.extend(response.json()["values"])
            total = response.json()["total"]
            skip += limit

            if skip >= total:
                break

        return events
