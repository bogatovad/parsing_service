"""
Django management команда для исправления ACL прав доступа к старым изображениям в MinIO
"""

import boto3
from django.core.management.base import BaseCommand
from django.conf import settings
from botocore.exceptions import ClientError


class Command(BaseCommand):
    help = "Исправляет ACL права доступа к старым изображениям в MinIO"

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("Начинаем исправление ACL для старых изображений...")
        )

        # Получаем настройки из Django settings
        minio_endpoint = settings.AWS_S3_ENDPOINT_URL
        minio_access_key = settings.AWS_ACCESS_KEY_ID
        minio_secret_key = settings.AWS_SECRET_ACCESS_KEY
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME

        # Создаем S3 клиент для работы с MinIO
        s3_client = boto3.client(
            "s3",
            endpoint_url=minio_endpoint,
            aws_access_key_id=minio_access_key,
            aws_secret_access_key=minio_secret_key,
            region_name="us-east-1",
        )

        try:
            self.stdout.write(f"Bucket: {bucket_name}")
            self.stdout.write(f"Endpoint: {minio_endpoint}")

            # Получаем список всех объектов в bucket
            paginator = s3_client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=bucket_name)

            updated_count = 0
            error_count = 0

            for page in pages:
                if "Contents" not in page:
                    self.stdout.write(
                        self.style.WARNING("Bucket пустой или нет доступа к файлам")
                    )
                    continue

                for obj in page["Contents"]:
                    file_key = obj["Key"]

                    try:
                        # Обновляем ACL для каждого файла на public-read
                        s3_client.put_object_acl(
                            Bucket=bucket_name, Key=file_key, ACL="public-read"
                        )

                        updated_count += 1
                        if updated_count % 10 == 0:  # Выводим прогресс каждые 10 файлов
                            self.stdout.write(f"Обработано {updated_count} файлов...")

                    except ClientError as e:
                        error_count += 1
                        self.stdout.write(
                            self.style.ERROR(
                                f"Ошибка обновления ACL для {file_key}: {e}"
                            )
                        )
                        continue

            self.stdout.write(self.style.SUCCESS("\n=== Результаты ==="))
            self.stdout.write(
                self.style.SUCCESS(f"Успешно обновлено: {updated_count} файлов")
            )

            if error_count > 0:
                self.stdout.write(self.style.WARNING(f"Ошибок: {error_count}"))

            if updated_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        "✓ Все старые изображения теперь должны быть доступны публично!"
                    )
                )

        except ClientError as e:
            self.stdout.write(self.style.ERROR(f"Ошибка при работе с MinIO: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Неожиданная ошибка: {e}"))
