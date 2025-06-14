from frameworks_and_drivers.django.parsing.data_manager.models import (
    Tags,
    Content,
)
from interface_adapters.gateways.npl_base_gateway.base_nlp_processor import (
    NLPProcessorBase,
)
from interface_adapters.gateways.parsing_base_gateway.base_gateway import BaseGateway
from interface_adapters.repositories.base_content_repository import (
    ContentRepositoryProtocol,
)
from usecases.places.data import arr
from django.core.files.base import ContentFile
import requests
import logging


class GetPlacesUsecase:
    def __init__(
        self,
        gateway: BaseGateway,
        nlp_processor: NLPProcessorBase,
        content_repo: ContentRepositoryProtocol,
        file_repo,
    ):
        self.gateway = gateway
        self.nlp_processor = nlp_processor
        self.content_repo = content_repo
        self.file_repo = file_repo

    def execute(self):
        unique_ids = self.content_repo.get_all_unique_ids()

        for line in arr:
            place = line
            unique_id = str(place["id"]) + "place"

            if unique_id in unique_ids:
                continue

            print(f"{place=}")
            name = place["name"]
            description = place["description"]
            location = place["address"]
            contact = [{"phone": place.get("phone", "-")}]
            city = "nn"
            category_name = self.nlp_processor.determine_category(
                description + name, "category_prompt_place"
            )

            # Если NLP не смог определить категорию, используем категорию по умолчанию
            if not category_name:
                category_name = "Места"

            print(f"Определена категория: {category_name}")

            # Download image
            image_url = place["image"]
            image_content = None
            if image_url:
                try:
                    response = requests.get(image_url, timeout=10)
                    if response.status_code == 200:
                        content_type = response.headers.get("content-type", "")
                        if content_type.startswith("image/"):
                            image_content = ContentFile(response.content)
                        else:
                            logging.error(
                                f"Invalid content type for image {image_url}: {content_type}"
                            )
                    else:
                        logging.error(
                            f"Failed to download image {image_url}, status code: {response.status_code}"
                        )
                except requests.exceptions.Timeout:
                    logging.error(f"Timeout while downloading image from {image_url}")
                except Exception as e:
                    logging.error(
                        f"Error downloading image for {name} from {image_url}: {e}"
                    )
            else:
                logging.warning(f"No image URL provided for {name}")

            # Create Content object
            content = Content.objects.create(
                name=name,
                description=description,
                location=location,
                contact=contact,
                date_start=None,
                date_end=None,
                time=None,
                cost=None,
                city=city,
                unique_id=unique_id,
            )

            # Обрабатываем тег (используем единый подход)
            if category_name:
                try:
                    category_name = category_name.strip()
                    tag_for_save = Tags.objects.filter(
                        name__iexact=category_name, macro_category="places"
                    ).first()

                    if not tag_for_save:
                        tag_for_save = Tags.objects.create(
                            name=category_name, description=f"Tag for {name}"
                        )
                        print(f"Создан новый тег: {category_name}")

                    content.tags.add(tag_for_save)
                except Exception as tag_error:
                    logging.warning(
                        f"Ошибка при сохранении тега {category_name}: {str(tag_error)}"
                    )

            # Save image if downloaded
            if image_content:
                filename = f"{unique_id}.jpg"
                content.image.save(filename, image_content, save=True)

            content.save()

            logging.info(f"Успешно сохранено место: {name}")
            print(f"Добавлено: {name}")
