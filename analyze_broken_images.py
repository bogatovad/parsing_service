#!/usr/bin/env python3
"""
Скрипт для анализа проблемных изображений в MinIO
"""

import os
import requests
from minio import Minio


def analyze_broken_images():
    # Получаем настройки из переменных окружения
    minio_endpoint = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
    minio_access_key = os.getenv("MINIO_ROOT_USER", "minioadmin")
    minio_secret_key = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
    bucket_name = os.getenv("MINIO_BUCKET_NAME", "afisha-files")

    print("=== Анализ проблемных изображений ===")
    print(f"Bucket: {bucket_name}")
    print()

    # Создаем клиент MinIO
    minio_endpoint_clean = minio_endpoint.replace("http://", "").replace("https://", "")
    client = Minio(
        minio_endpoint_clean,
        access_key=minio_access_key,
        secret_key=minio_secret_key,
        secure=False,
    )

    try:
        # Получаем список всех изображений
        objects = list(client.list_objects(bucket_name, prefix="images/"))

        print(f"Всего найдено изображений: {len(objects)}")
        print()

        working_images = []
        broken_images = []

        # Тестируем каждое изображение
        for i, obj in enumerate(objects):
            file_key = obj.object_name

            if i % 50 == 0:  # Показываем прогресс каждые 50 файлов
                print(f"Проверено {i}/{len(objects)} файлов...")

            # Тестируем доступ через afishabot.ru (ваш рабочий URL)
            test_url = f"https://afishabot.ru/{bucket_name}/{file_key}"

            try:
                response = requests.head(test_url, timeout=5)
                if response.status_code == 200:
                    working_images.append(
                        {
                            "file_key": file_key,
                            "size": obj.size,
                            "last_modified": obj.last_modified,
                            "etag": obj.etag,
                        }
                    )
                else:
                    broken_images.append(
                        {
                            "file_key": file_key,
                            "status_code": response.status_code,
                            "size": obj.size,
                            "last_modified": obj.last_modified,
                            "etag": obj.etag,
                        }
                    )
            except Exception as e:
                broken_images.append(
                    {
                        "file_key": file_key,
                        "error": str(e),
                        "size": obj.size,
                        "last_modified": obj.last_modified,
                        "etag": obj.etag,
                    }
                )

        print("\n=== Результаты анализа ===")
        print(
            f"Работающих изображений: {len(working_images)} ({len(working_images)/len(objects)*100:.1f}%)"
        )
        print(
            f"Проблемных изображений: {len(broken_images)} ({len(broken_images)/len(objects)*100:.1f}%)"
        )

        if broken_images:
            print("\n=== Анализ проблемных изображений ===")

            # Анализируем размеры файлов
            broken_sizes = [img["size"] for img in broken_images]
            working_sizes = [img["size"] for img in working_images]

            print(
                f"Средний размер проблемных файлов: {sum(broken_sizes)/len(broken_sizes):.0f} байт"
            )
            print(
                f"Средний размер рабочих файлов: {sum(working_sizes)/len(working_sizes):.0f} байт"
            )

            # Анализируем даты
            broken_dates = [img["last_modified"] for img in broken_images]
            working_dates = [img["last_modified"] for img in working_images]

            print(f"Самый старый проблемный файл: {min(broken_dates)}")
            print(f"Самый новый проблемный файл: {max(broken_dates)}")
            print(f"Самый старый рабочий файл: {min(working_dates)}")
            print(f"Самый новый рабочий файл: {max(working_dates)}")

            # Анализируем имена файлов
            print("\n=== Примеры проблемных файлов ===")
            for i, img in enumerate(broken_images[:10]):  # Показываем первые 10
                print(f"{i+1}. {img['file_key']}")
                print(f"   Размер: {img['size']} байт")
                print(f"   Дата: {img['last_modified']}")
                if "status_code" in img:
                    print(f"   Статус: {img['status_code']}")
                if "error" in img:
                    print(f"   Ошибка: {img['error']}")
                print()

            # Поиск паттернов в именах
            broken_names = [img["file_key"] for img in broken_images]

            # Проверяем наличие специальных символов
            special_chars_count = 0
            for name in broken_names:
                if any(char in name for char in ["%", "+", " ", "&", "?", "#"]):
                    special_chars_count += 1

            if special_chars_count > 0:
                print(
                    f"Файлов со специальными символами: {special_chars_count}/{len(broken_names)}"
                )

            # Проверяем расширения
            extensions = {}
            for name in broken_names:
                ext = name.split(".")[-1].lower()
                extensions[ext] = extensions.get(ext, 0) + 1

            print(f"Расширения проблемных файлов: {extensions}")

        else:
            print("\n✓ Все изображения работают корректно!")

    except Exception as e:
        print(f"Ошибка при анализе: {e}")


if __name__ == "__main__":
    analyze_broken_images()
