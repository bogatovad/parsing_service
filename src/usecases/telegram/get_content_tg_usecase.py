import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from dateutil.parser import parse

from interface_adapters.presenters.schemas import ContentPydanticSchema
from interface_adapters.gateways.parsing_base_gateway.base_gateway import BaseGateway
from interface_adapters.repositories.base_content_repository import (
    ContentRepositoryProtocol,
)
from interface_adapters.gateways.npl_base_gateway.base_nlp_processor import (
    NLPProcessorBase,
)

# Настройка логгера
logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Результат обработки контента"""

    success: bool
    content: Optional[ContentPydanticSchema] = None
    error: Optional[str] = None


class GetContentTgUseCase:
    """
    UseCase для обработки контента из Telegram каналов:
     1) Сканирует каналы (gateway.fetch_content)
     2) Прогоняет текст через NLP
     3) Формирует ContentPydanticSchema
     4) Проверяет дубликаты через репозиторий
     5) Сохраняет в репозиторий
    """

    def __init__(
        self,
        gateway: BaseGateway,
        nlp_processor: NLPProcessorBase,
        content_repo: ContentRepositoryProtocol,
        file_repo: Any,
    ):
        self.gateway = gateway
        self.nlp_processor = nlp_processor
        self.content_repo = content_repo
        self.file_repo = file_repo

    def execute(self) -> List[ContentPydanticSchema]:
        """Основной метод обработки контента"""
        results: List[ContentPydanticSchema] = []

        try:
            sources = self.gateway.get_sources()
            logger.info(f"Получено {len(sources)} источников для обработки")

            for source, city in sources:
                try:
                    processed = self._process_source(source, city)
                    results.extend(processed)
                except Exception as e:
                    logger.error(f"Ошибка при обработке источника {source}: {str(e)}")
                    continue

            return results

        except Exception as e:
            logger.error(f"Критическая ошибка в execute: {str(e)}")
            return results

    def _process_source(self, source: str, city: str) -> List[ContentPydanticSchema]:
        """Обработка одного источника"""
        results: List[ContentPydanticSchema] = []

        try:
            logger.info(f"Обработка канала: {source} (город: {city})")
            raw_contents = self.gateway.fetch_content(source, city)

            if not raw_contents:
                logger.debug(f"Нет сообщений в канале {source}")
                return results

            logger.info(f"Получено {len(raw_contents)} сообщений из {source}")

            # Получаем список существующих unique_id для проверки дубликатов
            existing_unique_ids = self.content_repo.get_all_unique_ids()
            logger.info(f"В базе уже есть {len(existing_unique_ids)} событий")

            # Фильтруем сырые данные - убираем дубликаты ДО дорогой NLP обработки
            filtered_raw_contents = []
            for raw in raw_contents:
                event_id = raw.get("event_id", "")
                channel = raw.get("channel", "")
                unique_id = f"{event_id}{channel}"

                if unique_id not in existing_unique_ids:
                    filtered_raw_contents.append(raw)
                    existing_unique_ids.append(
                        unique_id
                    )  # Добавляем, чтобы избежать дубликатов в рамках одного запуска
                else:
                    logger.debug(f"Пропускаем дубликат с unique_id: {unique_id}")

            logger.info(
                f"После фильтрации дубликатов осталось {len(filtered_raw_contents)} сообщений для обработки"
            )

            # Теперь обрабатываем только уникальные сообщения
            for raw in filtered_raw_contents:
                try:
                    processed_events = self.nlp_processor.process_post(raw)

                    if not processed_events:
                        continue

                    for evt in processed_events:
                        result = self._process_single_event(evt, raw, city)
                        if result.success and result.content:
                            results.append(result.content)
                        else:
                            logger.warning(
                                f"Не удалось обработать событие: {result.error}"
                            )

                except Exception as e:
                    logger.error(f"Ошибка при обработке сообщения: {str(e)}")
                    continue

            return results

        except Exception as e:
            logger.error(f"Ошибка при обработке источника {source}: {str(e)}")
            return results

    def _process_single_event(
        self, event: Dict[str, Any], raw: Dict[str, Any], city: str
    ) -> ProcessingResult:
        """Обработка одного события"""
        try:
            content = self._create_schema(event, raw, city)

            if not content:
                return ProcessingResult(
                    success=False, error="Не удалось создать схему контента"
                )

            self.content_repo.save_one_content(content)
            logger.info(f"Сохранено новое событие: {content.name}")
            return ProcessingResult(success=True, content=content)

        except Exception as e:
            return ProcessingResult(
                success=False, error=f"Ошибка при обработке события: {str(e)}"
            )

    def _create_schema(
        self, event: Dict[str, Any], raw: Dict[str, Any], city: str
    ) -> Optional[ContentPydanticSchema]:
        """Создание схемы контента из данных события"""
        try:
            event_id = raw.get("event_id", "")
            channel = raw.get("channel", "")
            unique_id = f"{event_id}{channel}"
            name = event.get("name")

            if not name:
                logger.warning("Событие без названия, пропускаем")
                return None

            description = event.get("description", "Описание отсутствует")
            tags = event.get("category", []) or event.get("tags", [])
            image = event.get("image", b"")
            contact = event.get("contact", {})

            if isinstance(contact, dict):
                contact = [contact]
            elif not isinstance(contact, list):
                contact = [{}]

            date_start = self._maybe_parse_date(event.get("data_start"))
            date_end = self._maybe_parse_date(event.get("data_end", date_start))

            if date_end < date_start:
                date_end = date_start

            # Валидация дат - пропускаем устаревшие события
            if not self._is_event_valid(date_start, date_end):
                logger.info(f"Пропускаем устаревшее событие Telegram: {name}")
                return None

            time_ = event.get("time", "00:00")
            location = event.get("location", "Место не указано")
            cost = event.get("cost", 0)

            try:
                cost = (
                    int(cost)
                    if isinstance(cost, (int, str)) and str(cost).isdigit()
                    else 0
                )
            except (ValueError, TypeError):
                cost = 0

            return ContentPydanticSchema(
                name=name,
                description=description,
                tags=tags,
                image=image,
                contact=contact,
                date_start=date_start,
                date_end=date_end,
                time=time_,
                location=location,
                cost=cost,
                city=city,
                unique_id=unique_id,
            )

        except Exception as e:
            logger.error(f"Ошибка при создании схемы: {str(e)}")
            return None

    @staticmethod
    def _maybe_parse_date(value: Any) -> datetime:
        """Безопасный парсинг даты"""
        if isinstance(value, datetime):
            return value

        if isinstance(value, str):
            try:
                return parse(value)
            except Exception as e:
                logger.debug(f"Ошибка парсинга даты '{value}': {str(e)}")

        return datetime.now()

    @staticmethod
    def _is_event_valid(date_start, date_end):
        """
        Проверяет, что событие не устарело.
        Возвращает False для событий которые уже завершились.
        """
        try:
            current_date = datetime.now()

            # Если есть дата окончания, проверяем её
            if date_end and isinstance(date_end, datetime):
                return current_date <= date_end

            # Если нет даты окончания, проверяем дату начала
            if isinstance(date_start, datetime):
                return current_date.date() <= date_start.date()

            # Если даты не datetime объекты, считаем событие валидным
            return True

        except Exception as e:
            logger.error(f"Ошибка при валидации даты: {e}")
            return True  # В случае ошибки не блокируем событие
