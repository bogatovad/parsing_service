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
import random
import requests


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
        unique_names = []

        for line in arr:
            place = line

            if place.get("name") in unique_names:
                continue
            else:
                unique_names.append(place.get("name"))

            print(f"{place=}")
            name = place["name"]
            description = place["description"]
            location = place["address"]
            contact = [{"phone": place.get("phone", "-")}]
            city = "nn"
            unique_id = str(place["id"]) + str(random.randint(1, 10000))
            category_name = self.nlp_processor.determine_category(
                description + name, "category_prompt_place"
            )

            # Create or get tag
            tag_obj = Tags.objects.filter(name=category_name)
            tag_obj = tag_obj.first()
            print(f"{tag_obj=}")

            # Download image
            image_url = place["image"]
            image_content = None
            if image_url:
                try:
                    response = requests.get(image_url)
                    if response.status_code == 200:
                        image_content = ContentFile(response.content)
                except Exception as e:
                    print(f"Ошибка загрузки изображения для {name}: {e}")

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

            # Add tag
            content.tags.add(tag_obj)

            # Save image if downloaded
            if image_content:
                filename = f"{unique_id}.jpg"
                content.image.save(filename, image_content, save=True)

            content.save()

            print(f"Добавлено: {name}")
