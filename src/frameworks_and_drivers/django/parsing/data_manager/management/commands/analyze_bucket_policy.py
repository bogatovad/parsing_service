"""
Django management команда для анализа bucket policy
"""

import json
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from minio import Minio
from minio.error import S3Error


class Command(BaseCommand):
    help = "Анализирует bucket policy и доступность изображений"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Анализируем bucket policy..."))

        # Получаем настройки из Django settings
        minio_endpoint = settings.AWS_S3_ENDPOINT_URL
        minio_access_key = settings.AWS_ACCESS_KEY_ID
        minio_secret_key = settings.AWS_SECRET_ACCESS_KEY
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME

        self.stdout.write("\n=== Настройки ===")
        self.stdout.write(f"MinIO Endpoint: {minio_endpoint}")
        self.stdout.write(f"Bucket: {bucket_name}")
        self.stdout.write(f"Access Key: {minio_access_key}")

        # Создаем клиент MinIO
        minio_endpoint_clean = minio_endpoint.replace("http://", "").replace(
            "https://", ""
        )
        client = Minio(
            minio_endpoint_clean,
            access_key=minio_access_key,
            secret_key=minio_secret_key,
            secure=False,
        )

        try:
            # 1. Проверяем существование bucket'а
            self.stdout.write("\n=== Проверка bucket'а ===")
            if client.bucket_exists(bucket_name):
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Bucket '{bucket_name}' существует")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"✗ Bucket '{bucket_name}' НЕ существует!")
                )
                return

            # 2. Получаем и анализируем bucket policy
            self.stdout.write("\n=== Анализ bucket policy ===")
            try:
                policy_json = client.get_bucket_policy(bucket_name)
                policy = json.loads(policy_json)

                self.stdout.write(self.style.SUCCESS("✓ Bucket policy установлена"))
                self.stdout.write(
                    f"Версия политики: {policy.get('Version', 'Не указана')}"
                )

                statements = policy.get("Statement", [])
                self.stdout.write(f"Количество правил (statements): {len(statements)}")

                for i, statement in enumerate(statements, 1):
                    self.stdout.write(f"\n--- Правило {i} ---")
                    self.stdout.write(f"Эффект: {statement.get('Effect', 'Не указан')}")
                    self.stdout.write(
                        f"Principal: {statement.get('Principal', 'Не указан')}"
                    )
                    self.stdout.write(
                        f"Action: {statement.get('Action', 'Не указано')}"
                    )
                    self.stdout.write(
                        f"Resource: {statement.get('Resource', 'Не указан')}"
                    )

                    # Проверяем корректность правил
                    effect = statement.get("Effect")
                    principal = statement.get("Principal", {})
                    actions = statement.get("Action", [])
                    resource = statement.get("Resource", "")

                    if effect != "Allow":
                        self.stdout.write(
                            self.style.WARNING(
                                f"  ⚠ Внимание: Effect не равен 'Allow': {effect}"
                            )
                        )

                    # Проверяем Principal - может быть "*" или ["*"]
                    if isinstance(principal, dict):
                        aws_principal = principal.get("AWS")
                        if aws_principal != "*" and aws_principal != ["*"]:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"  ⚠ Внимание: Principal не равен '*' или ['*']: {principal}"
                                )
                            )

                    if isinstance(actions, list):
                        if "s3:GetObject" not in actions:
                            self.stdout.write(
                                self.style.WARNING(
                                    "  ⚠ Внимание: s3:GetObject отсутствует в действиях"
                                )
                            )
                    elif isinstance(actions, str):
                        if actions != "s3:GetObject":
                            self.stdout.write(
                                self.style.WARNING(
                                    f"  ⚠ Внимание: действие не s3:GetObject: {actions}"
                                )
                            )

                    expected_resource = f"arn:aws:s3:::{bucket_name}/*"
                    # Resource может быть строкой или списком
                    if "GetObject" in str(actions):
                        resource_ok = resource == expected_resource or resource == [
                            expected_resource
                        ]
                        if not resource_ok:
                            self.stdout.write(
                                self.style.WARNING(
                                    "  ⚠ Внимание: Resource не соответствует ожидаемому:"
                                )
                            )
                            self.stdout.write(f"    Ожидается: {expected_resource}")
                            self.stdout.write(f"    Получено: {resource}")

            except S3Error as e:
                if "NoSuchBucketPolicy" in str(e):
                    self.stdout.write(
                        self.style.ERROR("✗ Bucket policy НЕ установлена!")
                    )
                    self.stdout.write(
                        "Рекомендация: запустите python manage.py setup_bucket_policy"
                    )
                    return
                else:
                    self.stdout.write(
                        self.style.ERROR(f"✗ Ошибка получения policy: {e}")
                    )
                    return

            # 3. Тестируем доступ к конкретным файлам
            self.stdout.write("\n=== Тестирование доступа к файлам ===")

            # Получаем список файлов (первые 10)
            objects = []
            for obj in client.list_objects(bucket_name, prefix="images/"):
                objects.append(obj)
                if len(objects) >= 10:
                    break

            if not objects:
                self.stdout.write(
                    self.style.WARNING("Нет файлов в папке images/ для тестирования")
                )
            else:
                working_count = 0
                broken_count = 0

                for obj in objects:
                    file_key = obj.object_name

                    # Тестируем прямой доступ к MinIO
                    direct_url = f"{minio_endpoint}/{bucket_name}/{file_key}"

                    try:
                        response = requests.head(direct_url, timeout=5)
                        if response.status_code == 200:
                            working_count += 1
                            self.stdout.write(self.style.SUCCESS(f"✓ {file_key}"))
                        else:
                            broken_count += 1
                            self.stdout.write(
                                self.style.ERROR(
                                    f"✗ {file_key} - статус: {response.status_code}"
                                )
                            )

                            # Дополнительная диагностика для проблемных файлов
                            try:
                                # Проверяем метаданные объекта
                                stat = client.stat_object(bucket_name, file_key)
                                self.stdout.write(f"    Размер: {stat.size} байт")
                                self.stdout.write(f"    Тип: {stat.content_type}")
                                self.stdout.write(f"    ETag: {stat.etag}")
                                self.stdout.write(
                                    f"    Дата модификации: {stat.last_modified}"
                                )
                            except Exception as stat_error:
                                self.stdout.write(
                                    f"    Ошибка получения метаданных: {stat_error}"
                                )

                    except Exception as e:
                        broken_count += 1
                        self.stdout.write(
                            self.style.ERROR(f"✗ {file_key} - ошибка: {e}")
                        )

                self.stdout.write("\n=== Результаты тестирования ===")
                total = working_count + broken_count
                working_percent = (working_count / total * 100) if total > 0 else 0
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Работающих: {working_count} ({working_percent:.1f}%)"
                    )
                )
                if broken_count > 0:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Неработающих: {broken_count} ({100-working_percent:.1f}%)"
                        )
                    )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Общая ошибка: {e}"))
