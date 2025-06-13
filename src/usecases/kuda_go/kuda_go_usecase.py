import re
from interface_adapters.gateways.parsing_base_gateway.base_gateway import BaseGateway
from interface_adapters.presenters.schemas import ContentPydanticSchema
from usecases.common import AbstractUseCase
from datetime import datetime
from interface_adapters.gateways.npl_base_gateway.base_nlp_processor import (
    NLPProcessorBase,
)
from interface_adapters.repositories.base_file_repository import FileRepositoryProtocol
from interface_adapters.repositories.base_content_repository import (
    ContentRepositoryProtocol,
)


class GetContentKudaGoUseCase(AbstractUseCase):
    def __init__(
        self,
        gateway: BaseGateway,
        content_repo: ContentRepositoryProtocol,
        nlp_processor: NLPProcessorBase,
        file_repo: FileRepositoryProtocol,
    ) -> None:
        self.gateway = gateway
        self.content_repo = content_repo
        self.file_repo = file_repo
        self.nlp_processor = nlp_processor

    def execute(self) -> list[ContentPydanticSchema]:
        raw_content = self.gateway.fetch_content()
        exists_unique_ids = self.content_repo.get_all_unique_ids()

        # Фильтруем сырые данные - убираем дубликаты ДО дорогой NLP обработки
        filtered_raw_content = []
        for element in raw_content:
            # Генерируем unique_id на основе сырых данных
            name = element.get("name", "Default Name FROM KUDA GO")
            date_start = element.get("date_start", datetime.now())
            location = element.get("location", "Unknown")

            # Создаем уникальный идентификатор из названия, даты и места
            if isinstance(date_start, datetime):
                date_str = date_start.strftime("%Y-%m-%d")
            else:
                date_str = str(date_start)

            unique_id = f"kudago_{name[:50]}_{date_str}_{location[:30]}"
            # Заменяем проблемные символы
            unique_id = re.sub(r"[^\w\-_]", "_", unique_id)

            if unique_id not in exists_unique_ids:
                filtered_raw_content.append((element, unique_id))
                exists_unique_ids.append(
                    unique_id
                )  # Добавляем, чтобы избежать дубликатов в рамках одного запуска
            else:
                print(f"Пропускаем дубликат KudaGo с unique_id: {unique_id}")

        print(
            f"После фильтрации дубликатов осталось {len(filtered_raw_content)} событий для NLP обработки"
        )

        # Теперь обрабатываем только уникальные события
        for element, unique_id in filtered_raw_content:
            processed_link_name = self.nlp_processor.generate_link_title(
                element.get("description")
            )
            processed_link_name = re.sub(r'^"|"$', "", processed_link_name)
            processed_categories = self.nlp_processor.determine_category(
                element.get("description")
            )

            name = element.get("name", "Default Name FROM KUDA GO")
            location = element.get("location", "Unknown")

            content_element = ContentPydanticSchema(
                name=name,
                description=element.get("description", "No description available"),
                tags=[processed_categories],
                image=element.get("image", b"gg"),
                contact=[{processed_link_name: element.get("url", "")}],
                date_start=element.get("date_start", datetime.now()),
                date_end=element.get("date_end", datetime.now()),
                time=element.get("time", "00:00"),
                location=location,
                cost=element.get("cost", 0),
                city=element.get("city", ""),
                unique_id=unique_id,
            )

            self.content_repo.save_one_content(content_element)
        return True
