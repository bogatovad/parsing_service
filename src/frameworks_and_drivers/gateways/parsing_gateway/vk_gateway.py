import time
import vk_api
from exeptions import ExeptionCheckAnswerKeys
import logging
import requests

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

    def create_vk_session(self) -> VkApiMethod:  # type: ignore
        vk_session = vk_api.VkApi(token=self.ACCESS_TOKEN)
        return vk_session.get_api()

    def loading_group_ids(self) -> list[str]:
        """Приводим из формата https://vk.com/torpedonn -> torpedonn"""
        return [group.strip().rsplit("/", 1)[-1] for group in self.group_url]

    def check_tokens(self) -> None:
        if not self.ACCESS_TOKEN:
            message = "Отсутствует обязательная переменная окружения {ACCESS_TOKEN}"
            logger.critical(message)
            raise ValueError("Нет переменной окружения SERVICE_KEY")

    def check_api_response_fields(self) -> None:
        """Проверка полей response на соответствие типу"""
        for i in range(len(self.response["items"])):
            if not isinstance(self.response["items"][i]["text"], str):
                message = "Поле text, пришло не ввиде строки."
                logger.error(message)
                raise ValueError(message)

    def check_api_response(self) -> None:
        """Проверяется валидность ответа API"""
        if not isinstance(self.response, dict):
            message = "Response пришёл не ввиде словаря"
            logger.error(message)
            raise TypeError("Response пришёл не ввиде словаря")

        if "items" not in self.response:
            message = "Ключа items нет в response"
            logger.error(message)
            raise ExeptionCheckAnswerKeys(message)

        for i in range(len(self.response["items"])):
            if "text" not in self.response["items"][i]:
                message = "В ответе нет ключа - text"
                logger.error(message)
                raise ExeptionCheckAnswerKeys(message)
        self.check_api_response_fields()

    def parsing(self, amount: int = None) -> None:
        """Парсинг"""
        vk = self.create_vk_session()
        self.amount_posts = amount if amount is not None else 3
        self.list_groups_id = self.loading_group_ids()
        self.list_response = []
        amount_pars_group = len(self.list_groups_id)
        if self.amount_posts > amount_pars_group:
            self.amount_posts_from_single_group = self.amount_posts // amount_pars_group
            amount_group_add_1post = self.amount_posts - (
                len(self.list_groups_id) * self.amount_posts_from_single_group
            )
            count = 0
            for group in self.list_groups_id:
                if count < amount_group_add_1post:
                    self.amount_posts_from_single_group += 1
                    self.response = vk.wall.get(
                        domain=group,
                        v=self.VERSION_VK_API,
                        count=self.amount_posts_from_single_group,
                    )
                    self.amount_posts_from_single_group -= 1
                    self.check_api_response()
                    self.list_response.append(self.response)
                    count += 1
                else:
                    self.response = vk.wall.get(
                        domain=group,
                        v=self.VERSION_VK_API,
                        count=self.amount_posts_from_single_group,
                    )
                    self.check_api_response()
                    self.list_response.append(self.response)
                    count += 1
        else:
            count = 0
            for group in self.list_groups_id:
                if count < self.amount_posts:
                    self.response = vk.wall.get(
                        domain=group, v=self.VERSION_VK_API, count=1
                    )
                    self.check_api_response()
                    self.list_response.append(self.response)
                count += 1

    def filter_content(self) -> None:
        """
        Приводим спаршенный контент в нужную форму.
        Пока что форма [{'id': int, 'text': str, orign_photo: bytes}]
        id - кастомный, просто нумерация
        """
        try:
            self.post_list = []
            for group_response in self.list_response:
                for i in range(len(group_response["items"])):
                    if "attachments" not in group_response["items"][i]:
                        raise ExeptionCheckAnswerKeys(
                            "В ответе нет ключа - attachments"
                        )
                    post = {}
                    text = group_response["items"][i]["text"]
                    if text:
                        post_text = text
                        for attachment in group_response["items"][i]["attachments"]:
                            if (
                                len(group_response["items"][i]["attachments"]) == 1
                                and attachment["type"] == "photo"
                            ):
                                post_photo_url = attachment["photo"]["orig_photo"][
                                    "url"
                                ]
                                response = requests.get(post_photo_url)
                                if response.status_code == 200:
                                    image_bytes = response.content
                                    print(type(image_bytes))
                                post["id"] = i
                                post["text"] = post_text
                                post["image"] = image_bytes
                                self.post_list.append(post)
        except (ExeptionCheckAnswerKeys, TypeError) as err:
            logger.error(err)

    def get_filter_data(self) -> list[dict]:
        return self.post_list

    def preaty_print(self):
        """Печать постов через чёрточку(для консоли)"""
        for i in range(len(self.post_list)):
            print("-------------------------------------------------------------")
            print(self.post_list[i])
            break


if __name__ == "__main__":
    start = time.time()
    parser_vk = ParsingVK()
    parser_vk.parsing(amount=5)
    parser_vk.filter_content()
    end = time.time()

    parser_vk.preaty_print()

    logger.info(f"Выполнилось за {end - start}")
