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
            "8d87a7478d87a7478d87a7478c8eb4a7b088d878d87a747e5ba6e8288b149e827b28dce",
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
            if not self.ACCESS_TOKEN:
                raise Exception("VK ACCESS_TOKEN is not set or empty")

            logger.debug(f"Using VK API version: {self.VERSION_VK_API}")
            logger.debug(
                f"Token length: {len(self.ACCESS_TOKEN) if self.ACCESS_TOKEN else 0}"
            )

            vk_session = vk_api.VkApi(token=self.ACCESS_TOKEN)
            vk = vk_session.get_api()

            # Проверим токен простым запросом
            try:
                test_response = vk.users.get(user_ids=1, v=self.VERSION_VK_API)
                logger.debug(f"Token validation successful: {test_response}")
            except Exception as token_test_error:
                logger.error(f"Token validation failed: {token_test_error}")
                raise Exception(f"Invalid VK token: {token_test_error}")

            logger.info("VK session created successfully")
            return vk
        except vk_api.exceptions.ApiError as e:
            logger.error(f"VK API Error during session creation: {e}")
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
            # Добавляем отладочное логирование для понимания структуры ответа
            logger.debug(
                f"API response keys: {list(response.keys()) if response else 'None'}"
            )

            # Проверяем, есть ли ошибка в ответе
            if "error" in response:
                logger.error(f"VK API returned error: {response['error']}")
                raise ExeptionCheckAnswerKeys(f"VK API error: {response['error']}")

            # Новая логика: VK API может возвращать данные напрямую или в обертке "response"
            if "response" in response:
                # Старый формат с оберткой
                api_response = response["response"]
                logger.debug("Using wrapped response format")
            else:
                # Новый формат без обертки - данные напрямую
                api_response = response
                logger.debug("Using direct response format")

            # Проверяем наличие ключа items в данных
            if "items" not in api_response:
                logger.error(f"Response structure: {api_response}")
                raise ExeptionCheckAnswerKeys("В ответе нет ключа - items")

            logger.debug(
                f"Successfully validated API response with {len(api_response.get('items', []))} items"
            )
            return api_response

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
            logger.debug(
                f"Making API call: wall.get(domain={group}, v={self.VERSION_VK_API}, count={count})"
            )
            response = vk.wall.get(domain=group, v=self.VERSION_VK_API, count=count)
            logger.debug(f"Raw API response type: {type(response)}")
            return self.validate_api_response(response)
        except vk_api.exceptions.ApiError as e:
            logger.error(f"VK API Error for group {group}: {e}")
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
            failed_groups = []

            logger.info(f"Will parse {amount} posts from {len(group_ids)} groups")

            if amount > len(group_ids):
                posts_per_group = amount // len(group_ids)
                extra_posts = amount % len(group_ids)

                for i, group in enumerate(group_ids):
                    posts_to_fetch = posts_per_group + (1 if i < extra_posts else 0)
                    logger.debug(f"Parsing group {group} ({i + 1}/{len(group_ids)})")
                    try:
                        response = self.parse_posts(vk, group, posts_to_fetch)
                        responses.append(response)
                        logger.debug(f"Successfully parsed group {group}")
                    except Exception as e:
                        logger.error(f"Failed to parse group {group}: {str(e)}")
                        failed_groups.append(group)
                        continue  # Продолжаем с следующей группой
            else:
                for i, group in enumerate(group_ids[:amount]):
                    logger.debug(f"Parsing group {group} ({i + 1}/{amount})")
                    try:
                        response = self.parse_posts(vk, group, 1)
                        responses.append(response)
                        logger.debug(f"Successfully parsed group {group}")
                    except Exception as e:
                        logger.error(f"Failed to parse group {group}: {str(e)}")
                        failed_groups.append(group)
                        continue  # Продолжаем с следующей группой

            logger.info(
                f"Successfully parsed {len(responses)} responses from VK groups"
            )
            if failed_groups:
                logger.warning(
                    f"Failed to parse {len(failed_groups)} groups: {failed_groups}"
                )

            self.responses = responses

        except Exception as e:
            logger.error(f"Critical error during VK parsing: {str(e)}")
            raise

    def filter_content(self) -> None:
        """Фильтрует и обрабатывает спаршенный контент."""
        logger.info("Starting content filtering")
        try:
            processed_posts = 0
            filtered_posts = []

            if not self.responses:
                logger.warning(
                    "No responses to filter - all groups may have failed to parse"
                )
                self.posts = []
                return

            for response_idx, response in enumerate(self.responses):
                try:
                    if not response or "items" not in response:
                        logger.warning(
                            f"Invalid response structure at index {response_idx}, skipping"
                        )
                        continue

                    for post_idx, post_data in enumerate(response["items"]):
                        try:
                            processed_post = self.process_post(post_data)
                            if processed_post:
                                filtered_posts.append(processed_post)
                                processed_posts += 1
                        except Exception as e:
                            logger.error(
                                f"Error processing post {post_idx} from response {response_idx}: {str(e)}"
                            )
                            continue  # Продолжаем с следующим постом

                except Exception as e:
                    logger.error(f"Error processing response {response_idx}: {str(e)}")
                    continue  # Продолжаем со следующим response

            self.posts = filtered_posts
            logger.info(f"Successfully filtered and processed {processed_posts} posts")

        except Exception as e:
            logger.error(f"Critical error during content filtering: {str(e)}")
            # Не поднимаем исключение, чтобы не сломать весь процесс
            self.posts = []

    def fetch_content(self) -> List[Dict[str, Any]]:
        """
        Получает контент из VK.

        Returns:
            List[Dict[str, Any]]: Список обработанных постов
        """
        try:
            self.parsing(amount=200)
            self.filter_content()

            result = [
                {
                    "id": post.id,
                    "text": post.text,
                    "image": post.image,
                    "city": "nn",  # Все VK группы относятся к Нижнему Новгороду
                }
                for post in self.posts
            ]

            logger.info(
                f"VK parsing completed. Successfully retrieved {len(result)} posts"
            )
            return result

        except Exception as e:
            logger.error(f"Error in fetch_content: {str(e)}")
            # Возвращаем пустой список вместо падения, если ничего не удалось спарсить
            return []

    def print_posts(self) -> None:
        """Выводит информацию о постах в консоль."""
        for post in self.posts:
            print("-" * 60)
            print(f"ID: {post.id}")
            print(f"Text: {post.text[:100]}...")
            print(f"Has image: {bool(post.image)}")
        print(f"\nTotal posts: {len(self.posts)}")
