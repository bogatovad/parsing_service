import vk_api
from frameworks_and_drivers.gateways.parsing_gateway.exeptions import (
    ExeptionCheckAnswerKeys,
)
import logging
import requests

from interface_adapters.gateways.parsing_base_gateway.base_gateway import BaseGateway

logger = logging.getLogger("my_logger")
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)


logger.addHandler(console_handler)


class ParsingVK(BaseGateway):
    def __init__(self, amount: int = None):
        self.amount_posts = amount if amount is not None else 150
        self.ACCESS_TOKEN = (
            "e55cb58be55cb58be55cb58b7be67746d4ee55ce55cb58b828c1488691a1e2af624bda5"
        )
        self.VERSION_VK_API = 5.199
        vk_session = vk_api.VkApi(token=self.ACCESS_TOKEN)
        self.vk = vk_session.get_api()
        self.groups_url = [
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
        self.amount_group_for_parsing = len(self.groups_url)

    def get_sources(self) -> list[str]:
        """Приводим из формата https://vk.com/torpedonn -> torpedonn"""
        return [group.strip().rsplit("/", 1)[-1] for group in self.groups_url]

    def parsing(self, group: str = None) -> None:
        """Парсинг"""
        self.list_response = []
        list_groups_id = self.get_sources()
        amount_posts_from_single_group = (
            self.amount_posts // self.amount_group_for_parsing
        )
        amount_group_add_1post = self.amount_posts - (
            self.amount_group_for_parsing * amount_posts_from_single_group
        )
        if list_groups_id.index(group) < amount_group_add_1post:
            self.response = self.vk.wall.get(
                domain=group,
                v=self.VERSION_VK_API,
                count=amount_posts_from_single_group + 1,
            )
            self.list_response.append(self.response)
        else:
            self.response = self.vk.wall.get(
                domain=group,
                v=self.VERSION_VK_API,
                count=amount_posts_from_single_group,
            )
            self.list_response.append(self.response)

    def filter_content(self) -> None:
        """
        Приводим спаршенный контент(несколько постов) из одной группы в нужную форму.
        Пока что форма [{'id': str, 'text': str, 'image': bytes}]
        id - hash соответствующего поста
        """
        try:
            self.post_list = []
            for group_response in self.list_response:
                for i in range(len(group_response["items"])):
                    if "attachments" not in group_response["items"][i]:
                        logger.info("В ответе нет ключа - attachments")
                        continue
                    post = {}
                    text = group_response["items"][i]["text"]
                    try:
                        id_hash = group_response["items"][i]["hash"]
                    except:
                        logger.info("Нет ключа hash")
                        continue
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
                                post["id"] = id_hash
                                post["text"] = post_text
                                if isinstance(image_bytes, bytes):
                                    post["image"] = image_bytes
                                self.post_list.append(post)
        except (ExeptionCheckAnswerKeys, TypeError) as err:
            logger.error(err)

    def fetch_content(self, group: str) -> list[dict]:
        self.parsing(group)
        self.filter_content()
        return self.post_list

    def preaty_print(self):
        """Печать постов через чёрточку(для консоли)"""
        for i in range(len(self.post_list)):
            print("-------------------------------------------------------------")
            print(self.post_list[i])
        print("Количество постов:", len(self.post_list))
