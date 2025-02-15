from interface_adapters.gateways.parsing_base_gateway.base_gateway import BaseGateway
from interface_adapters.gateways.npl_base_gateway.base_nlp_processor import (
    NLPProcessorBase,
)
from interface_adapters.presenters.schemas import ContentPydanticSchema
from usecases.common import AbstractUseCase
from datetime import datetime


class GetContentTgUseCase(AbstractUseCase):
    def __init__(
        self,
        gateway: BaseGateway,
        nlp_processor: NLPProcessorBase,
        content_repo,
        file_repo,
    ) -> None:
        print(
            "[ИНИЦИАЛИЗАЦИЯ] UseCase для получения контента из Telegram и обработки NLP инициализирован"
        )
        self.gateway = gateway
        self.nlp_processor = nlp_processor
        self.content_repo = content_repo
        self.file_repo = file_repo

    def execute(self) -> list[ContentPydanticSchema]:
        """
        Алгоритм:
         1. Получаем сырые данные из Telegram через gateway.
         2. Для каждого сообщения обрабатываем текст через nlp_processor.
         3. Если нейронка вернула список событий (список словарей), обрабатываем каждое.
         4. Приводим поля к ожидаемым типам (например, contact – к списку, cost – к целому).
         5. Формируем объект ContentPydanticSchema для каждого события.
         6. Возвращаем список объектов.
        """
        print("[ВЫПОЛНЕНИЕ] Получаем данные из gateway...")
        raw_contents = self.gateway.fetch_content()
        print(f"[ВЫПОЛНЕНИЕ] Получено сырых сообщений: {len(raw_contents)}")

        if not raw_contents:
            print("[ВЫПОЛНЕНИЕ] Новых сообщений не найдено, возвращаем пустой список")
            return []

        exists_content = self.content_repo.get_all_name_contents()
        raw_filter_content = [
            content
            for content in raw_contents
            if content.get("name") not in exists_content
        ]

        results = []
        for i, raw in enumerate(raw_filter_content):
            print(f"[ОБРАБОТКА] Обрабатываем сообщение {i + 1}/{len(raw_contents)}")
            # Получаем результат обработки: может быть словарём (одно событие) или списком словарей (несколько событий)
            processed_result = self.nlp_processor.process_post(raw)
            print(f"[ОБРАБОТКА] Результат обработки NLP: {processed_result}")

            if not processed_result:
                print(
                    f"[ОБРАБОТКА] Пропускаем сообщение {i + 1}: нет обработанных данных"
                )
                continue

            # Получаем картинку из исходного поста, чтобы прикрепить её ко всем событиям
            image_data = raw.get("image") or b""

            # Если результат – список событий
            if isinstance(processed_result, list):
                for event in processed_result:
                    # Если у события не задано поле image, добавляем общую картинку
                    if "image" not in event or event.get("image") is None:
                        event["image"] = image_data
                    content = self._create_schema_from_event(event)
                    if content:
                        print(
                            f"[РЕЗУЛЬТАТ] Создан объект ContentPydanticSchema: {content}"
                        )
                        results.append(content)
            # Если результат – одно событие (словарь)
            elif isinstance(processed_result, dict):
                if (
                    "image" not in processed_result
                    or processed_result.get("image") is None
                ):
                    processed_result["image"] = image_data
                content = self._create_schema_from_event(processed_result)
                if content:
                    print(f"[РЕЗУЛЬТАТ] Создан объект ContentPydanticSchema: {content}")
                    results.append(content)
            else:
                print(
                    f"[ОБРАБОТКА] Неизвестный формат данных от NLP для сообщения {i + 1}"
                )

        print(
            f"[ВЫПОЛНЕНИЕ] Обработка завершена. Всего обработано сообщений: {len(results)}"
        )
        self.content_repo.save_content(results)
        return results

    def _create_schema_from_event(self, event: dict) -> ContentPydanticSchema | None:
        """Вспомогательный метод для создания ContentPydanticSchema из словаря события."""
        try:
            # Нормализуем поле contact: если это не список, оборачиваем в список.
            contact = event.get("contact", [])
            if not isinstance(contact, list):
                contact = [contact]

            # todo: тут надо поправить и сделать по-нормальному
            contact_list_dict = {
                f"ссылка_{index}": _contact for index, _contact in enumerate(contact)
            }
            # Нормализуем поле cost: если оно пустое или не может быть приведено к int, устанавливаем 0.
            cost_raw = event.get("cost", 0)
            try:
                cost = int(cost_raw)
            except (ValueError, TypeError):
                cost = 0

            # Здесь можно добавить дополнительное преобразование дат, если они приходят в виде строк.
            return ContentPydanticSchema(
                name=event.get("name", "Default Name FROM TG"),
                description=event.get("description", "No description available"),
                tags=event.get("tags", []),
                image=event.get("image") or b"",
                contact=contact_list_dict,
                date_start=event.get("data_start", datetime.now()),
                date_end=event.get("data_end", datetime.now()),
                time=event.get("time", "00:00"),
                location=event.get("location", "Unknown"),
                cost=cost,
                city=event.get("city", "Unknown"),
            )
        except Exception as e:
            print(f"[ОБРАБОТКА] Ошибка при создании схемы: {e}")
            return None
