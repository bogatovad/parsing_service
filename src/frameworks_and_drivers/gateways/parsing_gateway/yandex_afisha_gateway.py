from typing import List, Dict

from interface_adapters.gateways.parsing_base_gateway.base_gateway import BaseGateway


class YandexAfishaGateway(BaseGateway):
    def __init__(self, client=None) -> None:
        """
        Инициализирует объект YandexAfishaGateway с клиентом.

        :param client: Клиент, используемый для выполнения запросов (например, bot или API клиент).
        """
        self.client = client

    def fetch_content(self) -> List[Dict]:
        """
        Метод для получения событий из Telegram. Должен быть реализован в соответствии с API.

        :return: Список событий в виде словарей.
        """
        # Здесь может быть запрос к API Яндекс Афиши, например:
        # response = self.client.get_updates() или другая логика взаимодействия с API
        # тут приведет пример данных.
        events = [
            {"event_id": 1, "name": "Event 1", "description": "Description 1"},
            {"event_id": 2, "name": "Event 2", "description": "Description 2"}
        ]
        return events
