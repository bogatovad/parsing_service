import vk_api
import os
from exeptions import ExeptionCheckAnswerKeys
import logging

logger = logging.getLogger("my_logger")
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)


logger.addHandler(console_handler)


class ParsingVK:
    def __init__(self):
        self.ACCESS_TOKEN = (
            "e55cb58be55cb58be55cb58b7be67746d4ee55ce55cb58b828c1488691a1e2af624bda5"
        )
        self.VERSION_VK_API = 5.199

    def create_vk_session(self):
        vk_session = vk_api.VkApi(token=self.ACCESS_TOKEN)
        vk = vk_session.get_api()
        return vk

    def loading_group_ids(self):
        """Приводим из формата https://vk.com/torpedonn -> torpedonn"""
        self.group_url = [
            "https://vk.com/afishann",
            "https://vk.com/afisha_nnov",
            "https://vk.com/afisha_52_region",
            "https://vk.com/bestgroupinmininuniver2025",
            "https://vk.com/nndaytoday",
            "https://vk.com/youth_ntt",
            "https://vk.com/kccopimunn",
            "https://vk.com/vysota_no",
            "https://vk.com/interestingnn",
            "https://vk.com/mp_unn",
            "https://vk.com/molodezh_no",
            "https://vk.com/minin_stv",
            "https://vk.com/it52info",
            "https://vk.com/moynnov",
            "https://vk.com/aiesec_nn",
            "https://vk.com/nizhnynovgorod_news",
            "https://vk.com/mininuniver",
            "https://vk.com/miloconcerthall",
            "https://vk.com/nizhny800",
            "https://vk.com/kreml_nn",
            "https://vk.com/equium_nn",
            "https://vk.com/standupclubnn",
            "https://vk.com/mininunivertk",
            "https://vk.com/minkultnn",
            "https://vk.com/mol_nn",
            "https://vk.com/tchk_unn",
            "https://vk.com/topgid_nnov",
        ]
        for group in self.group_url:
            groups_id = [group.strip().rsplit("/", 1)[-1] for group in self.group_url]
        return groups_id

    def check_tokens(self, ACCESS_TOKEN):
        if not ACCESS_TOKEN:
            message = "Отсутствует обязательная переменная окружения {ACCESS_TOKEN}"
            logger.critical(message)
            raise ValueError("Нет переменной окружения SERVICE_KEY")

    def check_api_response_fields(self):
        """Проверка полей response на соответствие типу"""
        for i in range(self.count_posts):
            if not isinstance(self.response["items"][i]["text"], str):
                message = "Поле text, пришло не ввиде строки."
                logger.error(message)
                raise ValueError(message)

    def check_api_response(self):
        """Проверяется валидность ответа API"""
        if not isinstance(self.response, dict):
            message = "Response пришёл не ввиде словаря"
            logger.error(message)
            raise TypeError("Response пришёл не ввиде словаря")

        if "items" not in self.response:
            message = "Ключа items нет в response"
            logger.error(message)
            raise ExeptionCheckAnswerKeys(message)

        for i in range(self.count_posts):
            if "text" not in self.response["items"][i]:
                message = "В ответе нет ключа text"
                logger.error(message)
                raise ExeptionCheckAnswerKeys(message)
        self.check_api_response_fields()

    def parsing(self, count=None):
        """Парсинг"""
        vk = self.create_vk_session()
        self.count_posts = count if count is not None else 3
        groups_id = self.loading_group_ids()
        self.response = vk.wall.get(
            domain=groups_id[26], v=self.VERSION_VK_API, count=self.count_posts
        )
        self.check_api_response()
        self.post_list = []

    def filter_content(self) -> list[dict]:
        """
        Приводим спаршенный контент в нужную форму.
        Пока что форма [{'id': 0, 'text': ''}]
        id - кастомный, просто нумерация
        """
        for i in range(self.count_posts):
            post = {}
            post_text = self.response["items"][i]["text"]
            post["id"] = i
            post["text"] = post_text
            self.post_list.append(post)

    def get_filter_data(self):
        return self.post_list

    def preaty_print(self):
        """Печать постов через чёрточку(для консоли)"""
        for i in range(len(self.post_list)):
            print("-------------------------------------------------------------")
            print(self.post_list[i])


if __name__ == "__main__":
    parser_vk = ParsingVK()
    parser_vk.parsing(count=3)
    parser_vk.filter_content()
    parser_vk.preaty_print()
    logger.info("Выполнилось")
