"""Wrapper S3-compatible (MinIO local ou Scaleway Object Storage)."""
from __future__ import annotations

from pathlib import Path

import boto3
from botocore.config import Config

from .config import settings


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        region_name=settings.s3_region,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        use_ssl=settings.s3_use_ssl,
        config=Config(signature_version="s3v4"),
    )


def ensure_bucket(bucket: str | None = None) -> str:
    bucket = bucket or settings.s3_bucket
    client = get_s3_client()
    existing = {b["Name"] for b in client.list_buckets().get("Buckets", [])}
    if bucket not in existing:
        client.create_bucket(Bucket=bucket)
    return bucket


def upload_file(local_path: Path, key: str, bucket: str | None = None) -> str:
    bucket = ensure_bucket(bucket)
    client = get_s3_client()
    client.upload_file(str(local_path), bucket, key)
    return f"s3://{bucket}/{key}"


def download_file(key: str, dest: Path, bucket: str | None = None) -> Path:
    bucket = bucket or settings.s3_bucket
    client = get_s3_client()
    dest.parent.mkdir(parents=True, exist_ok=True)
    client.download_file(bucket, key, str(dest))
    return dest
