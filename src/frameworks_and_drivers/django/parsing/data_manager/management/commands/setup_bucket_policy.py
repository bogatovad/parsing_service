"""
Django management команда для настройки публичной bucket policy в MinIO
"""

import json
from django.core.management.base import BaseCommand
from django.conf import settings
from minio import Minio
from minio.error import S3Error


class Command(BaseCommand):
    help = "Настраивает публичную bucket policy в MinIO для доступа к изображениям"

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("Начинаем настройку bucket policy в MinIO...")
        )

        # Получаем настройки из Django settings
        minio_endpoint = settings.AWS_S3_ENDPOINT_URL.replace("http://", "").replace(
            "https://", ""
        )
        minio_access_key = settings.AWS_ACCESS_KEY_ID
        minio_secret_key = settings.AWS_SECRET_ACCESS_KEY
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME

        self.stdout.write(f"MinIO Endpoint: {minio_endpoint}")
        self.stdout.write(f"Bucket: {bucket_name}")
        self.stdout.write(f"Access Key: {minio_access_key}")

        # Создаем клиент MinIO
        client = Minio(
            minio_endpoint,
            access_key=minio_access_key,
            secret_key=minio_secret_key,
            secure=False,  # Измените на True если используете HTTPS
        )

        # Политика для публичного доступа к файлам
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": ["s3:GetBucketLocation", "s3:ListBucket"],
                    "Resource": f"arn:aws:s3:::{bucket_name}",
                },
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{bucket_name}/*",
                },
            ],
        }

        try:
            # Проверяем, существует ли bucket
            if not client.bucket_exists(bucket_name):
                self.stdout.write(
                    self.style.WARNING(
                        f"Bucket {bucket_name} не существует. Создаем..."
                    )
                )
                client.make_bucket(bucket_name)
                self.stdout.write(self.style.SUCCESS(f"Bucket {bucket_name} создан."))

            # Устанавливаем политику
            client.set_bucket_policy(bucket_name, json.dumps(policy))
            self.stdout.write(
                self.style.SUCCESS(
                    f"Публичная политика установлена для bucket {bucket_name}"
                )
            )

            # Проверяем политику
            current_policy = client.get_bucket_policy(bucket_name)
            self.stdout.write("Текущая политика bucket:")
            self.stdout.write(json.dumps(json.loads(current_policy), indent=2))

            self.stdout.write(
                self.style.SUCCESS(
                    "\n✓ Все изображения в bucket теперь должны быть публично доступны!"
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    "Проверьте изображения: https://afishabot.ru/afisha-files/images/"
                )
            )

        except S3Error as e:
            self.stdout.write(self.style.ERROR(f"Ошибка при настройке MinIO: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Неожиданная ошибка: {e}"))
