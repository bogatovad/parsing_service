import vk_api
from frameworks_and_drivers.gateways.parsing_gateway.exeptions import (
    ExeptionCheckAnswerKeys,
)
import logging
import requests
import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from interface_adapters.gateways.parsing_base_gateway.base_gateway import BaseGateway
from vk_api.exceptions import ApiError

logger = logging.getLogger(__name__)


@dataclass
class VKPost:
    """Структура данных для хранения информации о посте VK"""

    id: str
    text: str
    image: Optional[bytes] = None


class ParsingVK(BaseGateway):
    """
    Парсер для получения контента из групп VK.

    Attributes:
        VERSION_VK_API: Версия API VK
        group_url: Список URL групп для парсинга
    """

    VERSION_VK_API = 5.199
    MAX_RETRIES = 3
    RETRY_DELAY = 60  # seconds

    def __init__(self):
        self.posts: List[VKPost] = []
        self.ACCESS_TOKEN = os.getenv(
            "VK_ACCESS_TOKEN",
            "e55cb58be55cb58be55cb58b7be67746d4ee55ce55cb58b828c1488691a1e2af624bda5",
        )
        if not self.ACCESS_TOKEN:
            raise ValueError("VK_ACCESS_TOKEN environment variable is not set")

        # Список групп для парсинга
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

    def handle_vk_error(self, error: ApiError, retry_count: int = 0) -> None:
        """
        Обрабатывает ошибки API VK.

        Args:
            error: Объект ошибки VK API
            retry_count: Текущее количество попыток

        Raises:
            ApiError: Если превышено максимальное количество попыток или ошибка неустранима
        """
        error_code = error.code
        error_msg = str(error)

        logger.error(f"VK API Error {error_code}: {error_msg}")

        if error_code == 8:  # Application is blocked
            logger.critical(
                "VK Application is blocked. Please check the access token or contact VK support."
            )
            raise
        elif error_code == 29:  # Rate limit reached
            if retry_count < self.MAX_RETRIES:
                import time

                time.sleep(self.RETRY_DELAY)
                return
            else:
                logger.error("Max retries reached for rate limit")
                raise
        else:
            raise

    def create_vk_session(self) -> vk_api.vk_api.VkApiMethod:
        """
        Создает сессию VK API.

        Returns:
            VkApiMethod: Объект для работы с API VK

        Raises:
            Exception: При ошибке создания сессии
        """
        logger.info("Creating VK session")
        try:
            vk_session = vk_api.VkApi(token=self.ACCESS_TOKEN)
            vk = vk_session.get_api()
            logger.info("VK session created successfully")
            return vk
        except vk_api.exceptions.ApiError as e:
            self.handle_vk_error(e)
        except Exception as e:
            logger.error(f"Error creating VK session: {str(e)}")
            raise

    def get_group_ids(self) -> List[str]:
        """
        Извлекает ID групп из их URL.

        Returns:
            List[str]: Список ID групп
        """
        logger.info("Loading group IDs")
        try:
            group_ids = [group.split("/")[-1] for group in self.group_url]
            logger.info(f"Successfully loaded {len(group_ids)} group IDs")
            return group_ids
        except Exception as e:
            logger.error(f"Error loading group IDs: {str(e)}")
            raise

    def validate_api_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Проверяет корректность ответа API VK.

        Args:
            response: Ответ от API VK

        Returns:
            Dict[str, Any]: Проверенный ответ

        Raises:
            ExeptionCheckAnswerKeys: Если структура ответа некорректна
        """
        try:
            if "response" not in response:
                raise ExeptionCheckAnswerKeys("В ответе нет ключа - response")
            if "items" not in response["response"]:
                raise ExeptionCheckAnswerKeys("В ответе нет ключа - items")
            return response["response"]
        except ExeptionCheckAnswerKeys as e:
            logger.error(f"API response validation failed: {str(e)}")
            raise

    def parse_posts(
        self,
        vk: vk_api.vk_api.VkApiMethod,
        group: str,
        count: int,
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Получает посты из группы VK.

        Args:
            vk: Объект для работы с API VK
            group: ID группы
            count: Количество постов для получения
            retry_count: Текущее количество попыток

        Returns:
            Dict[str, Any]: Ответ API с постами
        """
        try:
            response = vk.wall.get(domain=group, v=self.VERSION_VK_API, count=count)
            return self.validate_api_response(response)
        except vk_api.exceptions.ApiError as e:
            self.handle_vk_error(e, retry_count)
            if retry_count < self.MAX_RETRIES:
                return self.parse_posts(vk, group, count, retry_count + 1)
            raise
        except Exception as e:
            logger.error(f"Error parsing posts from group {group}: {str(e)}")
            raise

    def download_image(self, url: str) -> Optional[bytes]:
        """
        Загружает изображение по URL.

        Args:
            url: URL изображения

        Returns:
            Optional[bytes]: Содержимое изображения или None при ошибке
        """
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.content
            logger.warning(
                f"Failed to download image, status code: {response.status_code}"
            )
            return None
        except Exception as e:
            logger.error(f"Error downloading image: {str(e)}")
            return None

    def process_post(self, post_data: Dict[str, Any]) -> Optional[VKPost]:
        """
        Обрабатывает данные поста VK.

        Args:
            post_data: Данные поста из API VK

        Returns:
            Optional[VKPost]: Обработанный пост или None при ошибке
        """
        if "attachments" not in post_data:
            logger.debug("Post without attachments found, skipping")
            return None

        text = post_data.get("text", "")
        if not text:
            return None

        for attachment in post_data["attachments"]:
            if len(post_data["attachments"]) == 1 and attachment["type"] == "photo":
                photo_url = attachment["photo"]["orig_photo"]["url"]
                image_data = self.download_image(photo_url)
                if image_data:
                    return VKPost(id=post_data["hash"], text=text, image=image_data)
        return None

    def parsing(self, amount: Optional[int] = None) -> None:
        """
        Выполняет парсинг постов из групп VK.

        Args:
            amount: Количество постов для парсинга (по умолчанию 3)
        """
        logger.info("Starting VK parsing")
        try:
            vk = self.create_vk_session()
            amount = amount if amount is not None else 3
            group_ids = self.get_group_ids()
            responses = []

            logger.info(f"Will parse {amount} posts from {len(group_ids)} groups")

            if amount > len(group_ids):
                posts_per_group = amount // len(group_ids)
                extra_posts = amount % len(group_ids)

                for i, group in enumerate(group_ids):
                    posts_to_fetch = posts_per_group + (1 if i < extra_posts else 0)
                    logger.debug(f"Parsing group {group} ({i + 1}/{len(group_ids)})")
                    response = self.parse_posts(vk, group, posts_to_fetch)
                    responses.append(response)
            else:
                for i, group in enumerate(group_ids[:amount]):
                    logger.debug(f"Parsing group {group} ({i + 1}/{amount})")
                    response = self.parse_posts(vk, group, 1)
                    responses.append(response)

            logger.info(
                f"Successfully parsed {len(responses)} responses from VK groups"
            )
            self.responses = responses

        except Exception as e:
            logger.error(f"Error during VK parsing: {str(e)}")
            raise

    def filter_content(self) -> None:
        """Фильтрует и обрабатывает спаршенный контент."""
        logger.info("Starting content filtering")
        try:
            processed_posts = 0
            filtered_posts = []

            for response in self.responses:
                for post_data in response["items"]:
                    processed_post = self.process_post(post_data)
                    if processed_post:
                        filtered_posts.append(processed_post)
                        processed_posts += 1

            self.posts = filtered_posts
            logger.info(f"Successfully filtered and processed {processed_posts} posts")

        except Exception as e:
            logger.error(f"Error during content filtering: {str(e)}")
            raise

    def fetch_content(self) -> List[Dict[str, Any]]:
        """
        Получает контент из VK.

        Returns:
            List[Dict[str, Any]]: Список обработанных постов
        """
        self.parsing(amount=100)
        self.filter_content()
        return [
            {"id": post.id, "text": post.text, "image": post.image}
            for post in self.posts
        ]

    def print_posts(self) -> None:
        """Выводит информацию о постах в консоль."""
        for post in self.posts:
            print("-" * 60)
            print(f"ID: {post.id}")
            print(f"Text: {post.text[:100]}...")
            print(f"Has image: {bool(post.image)}")
        print(f"\nTotal posts: {len(self.posts)}")
