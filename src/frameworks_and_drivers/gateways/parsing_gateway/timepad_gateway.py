from typing import List, Dict

from interface_adapters.gateways.parsing_base_gateway.base_gateway import BaseGateway
import requests


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

        :return: Список событий в виде словарей.
        """
        params = {
            "fields": "ticket_types,location",
            "cities": "Нижний Новгород",
            "starts_at_min": "2025-01-25",
            "sort": "starts_at"
        }
        headers = {
            "Authorization": "Bearer 23ee52ea2569153a9b1abcaa24682020aa2363ba"
        }
        # todo: тут надо проверить, есть ли уже такие события в БД через event_ids_exclude
        api_url = "https://api.timepad.ru/v1/events"
        response = requests.get(api_url, params=params, headers=headers)
        response.raise_for_status()
        events = response.json()["values"]
        return events
