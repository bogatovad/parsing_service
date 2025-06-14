#!/usr/bin/env python3
"""
Скрипт для анализа политики MinIO bucket
"""

import json
import os
import requests
from minio import Minio
from minio.error import S3Error


def analyze_bucket_policy():
    # Получаем настройки из переменных окружения
    minio_endpoint = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
    minio_access_key = os.getenv("MINIO_ROOT_USER", "minioadmin")
    minio_secret_key = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
    bucket_name = os.getenv("MINIO_BUCKET_NAME", "afisha-files")

    print("=== Настройки ===")
    print(f"MinIO Endpoint: {minio_endpoint}")
    print(f"Bucket: {bucket_name}")
    print(f"Access Key: {minio_access_key}")
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
        # 1. Проверяем существование bucket'а
        print("=== Проверка bucket'а ===")
        if client.bucket_exists(bucket_name):
            print(f"✓ Bucket '{bucket_name}' существует")
        else:
            print(f"✗ Bucket '{bucket_name}' НЕ существует!")
            return

        # 2. Получаем и анализируем bucket policy
        print("\n=== Анализ bucket policy ===")
        try:
            policy_json = client.get_bucket_policy(bucket_name)
            policy = json.loads(policy_json)

            print("✓ Bucket policy установлена")
            print(f"Версия политики: {policy.get('Version', 'Не указана')}")

            statements = policy.get("Statement", [])
            print(f"Количество правил (statements): {len(statements)}")

            for i, statement in enumerate(statements, 1):
                print(f"\n--- Правило {i} ---")
                print(f"Эффект: {statement.get('Effect', 'Не указан')}")
                print(f"Principal: {statement.get('Principal', 'Не указан')}")
                print(f"Action: {statement.get('Action', 'Не указано')}")
                print(f"Resource: {statement.get('Resource', 'Не указан')}")

                # Проверяем корректность правил
                effect = statement.get("Effect")
                principal = statement.get("Principal", {})
                actions = statement.get("Action", [])
                resource = statement.get("Resource", "")

                if effect != "Allow":
                    print(f"  ⚠ Внимание: Effect не равен 'Allow': {effect}")

                if isinstance(principal, dict) and principal.get("AWS") != "*":
                    print(f"  ⚠ Внимание: Principal не равен '*': {principal}")

                if isinstance(actions, list):
                    if "s3:GetObject" not in actions:
                        print("  ⚠ Внимание: s3:GetObject отсутствует в действиях")
                elif isinstance(actions, str):
                    if actions != "s3:GetObject":
                        print(f"  ⚠ Внимание: действие не s3:GetObject: {actions}")

                expected_resource = f"arn:aws:s3:::{bucket_name}/*"
                if "GetObject" in str(actions) and resource != expected_resource:
                    print("  ⚠ Внимание: Resource не соответствует ожидаемому:")
                    print(f"    Ожидается: {expected_resource}")
                    print(f"    Получено: {resource}")

        except S3Error as e:
            if "NoSuchBucketPolicy" in str(e):
                print("✗ Bucket policy НЕ установлена!")
                print("Рекомендация: запустите python manage.py setup_bucket_policy")
                return
            else:
                print(f"✗ Ошибка получения policy: {e}")
                return

        # 3. Тестируем доступ к конкретным файлам
        print("\n=== Тестирование доступа к файлам ===")

        # Получаем список файлов
        objects = list(client.list_objects(bucket_name, prefix="images/", max_keys=10))

        if not objects:
            print("Нет файлов в папке images/ для тестирования")
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
                        print(f"✓ {file_key}")
                    else:
                        broken_count += 1
                        print(f"✗ {file_key} - статус: {response.status_code}")

                        # Дополнительная диагностика для проблемных файлов
                        try:
                            # Проверяем метаданные объекта
                            stat = client.stat_object(bucket_name, file_key)
                            print(f"    Размер: {stat.size} байт")
                            print(f"    Тип: {stat.content_type}")
                            print(f"    ETag: {stat.etag}")
                            print(f"    Дата модификации: {stat.last_modified}")
                        except Exception as stat_error:
                            print(f"    Ошибка получения метаданных: {stat_error}")

                except Exception as e:
                    broken_count += 1
                    print(f"✗ {file_key} - ошибка: {e}")

            print("\n=== Результаты тестирования ===")
            total = working_count + broken_count
            working_percent = (working_count / total * 100) if total > 0 else 0
            print(f"Работающих: {working_count} ({working_percent:.1f}%)")
            print(f"Неработающих: {broken_count} ({100-working_percent:.1f}%)")

        # 4. Проверяем настройки MinIO сервера
        print("\n=== Проверка настроек MinIO ===")
        try:
            # Проверяем доступность корневого эндпоинта
            root_response = requests.get(minio_endpoint, timeout=5)
            print(f"MinIO корневой эндпоинт доступен: {root_response.status_code}")
        except Exception as e:
            print(f"Проблема с доступностью MinIO: {e}")

    except Exception as e:
        print(f"Общая ошибка: {e}")


if __name__ == "__main__":
    analyze_bucket_policy()
