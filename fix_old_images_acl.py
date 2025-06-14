#!/usr/bin/env python3
"""
Скрипт для исправления ACL прав доступа к старым изображениям в MinIO
"""

import os
import boto3
from botocore.exceptions import ClientError


def fix_old_images_acl():
    # Получаем настройки из переменных окружения (уже загружены в Docker контейнере)
    minio_endpoint = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
    minio_access_key = os.getenv("MINIO_ROOT_USER", "minioadmin")
    minio_secret_key = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
    bucket_name = os.getenv("MINIO_BUCKET_NAME", "afisha-files")

    # Создаем S3 клиент для работы с MinIO
    s3_client = boto3.client(
        "s3",
        endpoint_url=minio_endpoint,
        aws_access_key_id=minio_access_key,
        aws_secret_access_key=minio_secret_key,
        region_name="us-east-1",  # MinIO использует этот регион по умолчанию
    )

    try:
        print(f"Начинаем обновление ACL для файлов в bucket: {bucket_name}")

        # Получаем список всех объектов в bucket
        paginator = s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=bucket_name)

        updated_count = 0
        error_count = 0

        for page in pages:
            if "Contents" not in page:
                print("Bucket пустой или нет доступа к файлам")
                continue

            for obj in page["Contents"]:
                file_key = obj["Key"]

                try:
                    # Обновляем ACL для каждого файла на public-read
                    s3_client.put_object_acl(
                        Bucket=bucket_name, Key=file_key, ACL="public-read"
                    )

                    updated_count += 1
                    print(f"✓ Обновлен ACL для: {file_key}")

                except ClientError as e:
                    error_count += 1
                    print(f"✗ Ошибка обновления ACL для {file_key}: {e}")
                    continue

        print("\n=== Результаты ===")
        print(f"Успешно обновлено: {updated_count} файлов")
        print(f"Ошибок: {error_count}")

        if updated_count > 0:
            print("\n✓ Все старые изображения теперь должны быть доступны публично!")
            print(
                "Проверьте ваши изображения: https://afishabot.ru/afisha-files/images/"
            )

    except ClientError as e:
        print(f"Ошибка при работе с MinIO: {e}")
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")


if __name__ == "__main__":
    fix_old_images_acl()
