#!/usr/bin/env python3
"""
Скрипт для настройки публичной политики MinIO bucket
"""

import json
import os
from minio import Minio
from minio.error import S3Error


def setup_minio_policy():
    # Получаем настройки из переменных окружения
    minio_endpoint = (
        os.getenv("MINIO_ENDPOINT", "http://minio:9000")
        .replace("http://", "")
        .replace("https://", "")
    )
    minio_access_key = os.getenv("MINIO_ROOT_USER", "minioadmin")
    minio_secret_key = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
    bucket_name = os.getenv("MINIO_BUCKET_NAME", "afisha-files")

    print(f"MinIO Endpoint: {minio_endpoint}")
    print(f"Bucket: {bucket_name}")
    print(f"Access Key: {minio_access_key}")

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
            print(f"Bucket {bucket_name} не существует. Создаем...")
            client.make_bucket(bucket_name)
            print(f"Bucket {bucket_name} создан.")

        # Устанавливаем политику
        client.set_bucket_policy(bucket_name, json.dumps(policy))
        print(f"Публичная политика установлена для bucket {bucket_name}")

        # Проверяем политику
        current_policy = client.get_bucket_policy(bucket_name)
        print("Текущая политика bucket:")
        print(json.dumps(json.loads(current_policy), indent=2))

    except S3Error as e:
        print(f"Ошибка при настройке MinIO: {e}")
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")


if __name__ == "__main__":
    setup_minio_policy()
