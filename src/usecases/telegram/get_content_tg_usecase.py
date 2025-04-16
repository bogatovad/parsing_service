import logging
from datetime import datetime
from dateutil.parser import parse

# Импорт dedup'а:
from usecases.telegram.dedup import check_and_add_event
# Импорт схемы (PydanticSchema)
from interface_adapters.presenters.schemas import ContentPydanticSchema
# Базовые классы (заглушки) — если у вас есть реальные, оставьте их.
from interface_adapters.gateways.parsing_base_gateway.base_gateway import BaseGateway
from interface_adapters.gateways.npl_base_gateway.base_nlp_processor import NLPProcessorBase

# Импорт Кандинского для генерации изображений
from usecases.telegram.kandinsky_api import generate_image_with_kandinsky

logging.basicConfig(level=logging.DEBUG)


class GetContentTgUseCase:
    """
    UseCase, который:
     1) Сканирует каналы (gateway.fetch_content)
     2) Прогоняет текст через NLP
     3) Генерирует изображение через Кандинский, если отсутствует
     4) Формирует ContentPydanticSchema
     5) Проверяет дубликаты (check_and_add_event)
     6) Сохраняет в репозиторий
    """
    def __init__(self, gateway: BaseGateway, nlp_processor: NLPProcessorBase, content_repo):
        self.gateway = gateway
        self.nlp_processor = nlp_processor
        self.content_repo = content_repo

    def execute(self):
        results = []
        sources = self.gateway.get_sources()
        logging.info(f"Список источников: {sources}")

        for source, city in sources:
            logging.info(f"Обрабатываем канал: {source} (город: {city})")
            raw_contents = self.gateway.fetch_content(source, city)
            logging.info(f"Получено {len(raw_contents)} сообщений из {source}")

            if not raw_contents:
                logging.debug("Список сообщений пуст, пропускаем этот канал.")
                continue

            # Для каждого сообщения → NLP
            for raw in raw_contents:
                processed_events = self.nlp_processor.process_post(raw)
                if not processed_events:
                    logging.debug("NLP вернуло пустой список для поста, пропускаем.")
                    continue

                # Исходная картинка, если есть
                image_data = raw.get("image") or b""

                for evt in processed_events:
                    # === Добавляем логику Кандинского ===
                    # Если нет картинки, пытаемся взять из raw
                    if not evt.get("image"):
                        evt["image"] = image_data
                        # Если по-прежнему нет, генерируем через Кандинский
                        if not evt["image"]:
                            prompt_text = f"{evt.get('name', '')} {evt.get('description', '')}"
                            evt["image"] = generate_image_with_kandinsky(prompt_text)

                    # Создаём Pydantic-схему
                    content = self._create_schema(evt, raw, city)
                    if not content:
                        logging.debug("Не удалось создать ContentPydanticSchema, пропускаем.")
                        continue

                    # Дедупликация
                    dedup_data = {
                        "name": content.name,
                        "date_start": content.date_start,
                        "time": content.time,
                        "location": content.location,
                    }
                    is_dup = check_and_add_event(dedup_data)
                    if is_dup:
                        logging.info(f"Событие дубликат: {content}")
                        continue

                    # Если не дубликат — сохраняем
                    logging.info(f"Сохраняем новое событие: {content}")
                    self.content_repo.save(content)
                    results.append(content)

        return results

    def _create_schema(self, event: dict, raw: dict, city: str) -> ContentPydanticSchema | None:
        """
        Приводит dict от нейросети к ContentPydanticSchema. Парсит даты, выставляет уникальный ID.
        """
        unique_id = raw.get("event_id", "") + raw.get("channel", "")

        name = event.get("name", "Default Name FROM TG")
        description = event.get("description", "No description available")
        tags = event.get("category", []) or event.get("tags", [])
        image = event.get("image", b"")
        contact = event.get("contact", {})

        date_start = self._maybe_parse_date(event.get("data_start", datetime.now()))
        date_end = self._maybe_parse_date(event.get("data_end", date_start))
        time_ = event.get("time", "00:00")
        location = event.get("location", "Unknown")
        cost_raw = event.get("cost", 0)

        # Преобразуем cost в int, если возможно
        try:
            cost = int(cost_raw)
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
            unique_id=unique_id
        )

    @staticmethod
    def _maybe_parse_date(value):
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return parse(value)
            except Exception:
                pass
        return datetime.now()  # fallback если не распарсилось
