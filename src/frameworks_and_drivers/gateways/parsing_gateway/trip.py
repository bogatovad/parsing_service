import json
import re
import requests
from django.core.files.base import ContentFile
from frameworks_and_drivers.django.parsing.data_manager.models import (
    Content,
    Tags,
    MacroCategory,
)

CATEGORY_RULES = [
    (r"парк|сквер|сад|заповедник", "Парк"),
    (r"музей|галерея|выставка|экспозиция", "Музей / Выставка"),
    (r"театр|тюз|драма", "Театр"),
    (r"ресторан|кафе|бар|пиццерия|бургер|стейк", "Ресторан / Кафе"),
    (r"кинотеатр", "Кино"),
    (r"цирк|зоопарк|аквапарк|батут|интерактивный", "Развлечения"),
    (r"клуб|караоке|концерт|паб|дискотека|холл", "Ночной клуб / Концерт"),
    (r"храм|церковь|собор|монастырь", "Храм / Религия"),
    (r"йога|фитнес|спорт", "Спорт"),
]


def determine_category(name, description):
    text = f"{name.lower()} {description.lower()}"
    for pattern, category in CATEGORY_RULES:
        if re.search(pattern, text):
            return category
    return "Другое"


def import_places(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            place = json.loads(line)

            name = place["name"]
            description = place["description"]
            location = place["address"]
            contact = {"phone": place.get("phone", "-")}
            city = "nn"
            unique_id = place["id"]
            category_name = determine_category(name, description)

            # Create or get tag
            mc = MacroCategory.objects.filter(name="places").first()
            tag_obj, _ = Tags.objects.get_or_create(
                name=category_name, macro_category=mc, description="test"
            )

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

            print(f"Добавлено: {name}")


import_places("../../../../places_fixed.json")
