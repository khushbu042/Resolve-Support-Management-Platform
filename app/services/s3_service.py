import boto3
from botocore.exceptions import ClientError
from functools import lru_cache

from app.core.settings import get_settings

settings = get_settings()
AWS_REGION = settings.s3_region
BUCKET_NAME = settings.s3_bucket_name

@lru_cache(maxsize=1)
def get_s3_client():
    return boto3.client(
        "s3",
        region_name=AWS_REGION,
    )


async def upload_file(file: str, object_key: str):
    s3_client = get_s3_client()
    s3_client.upload_fileobj(
        file,
        BUCKET_NAME,
        object_key,
    )

async def download_file(object_key: str, file_path: str):
    s3_client = get_s3_client()
    await s3_client.download_file(
        BUCKET_NAME,
        object_key,
        file_path,
    )

async def get_file(object_key: str):
    s3_client = get_s3_client()
    try:
        response = s3_client.get_object(
            Bucket=BUCKET_NAME,
            Key=object_key,
        )

        return response

    except ClientError as e:
        if e.response["Error"]["Code"] in ("NoSuchKey", "404"):
            raise FileNotFoundError("Attachment not found in S3")

        raise


async def delete_file(object_key: str):
    s3_client = get_s3_client()
    s3_client.delete_object(
        Bucket=BUCKET_NAME,
        Key=object_key,
    )

async def generate_download_url(object_key: str, expires_in: int = 3600):
    s3_client = get_s3_client()
    return s3_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": BUCKET_NAME,
            "Key": object_key,
        },
        ExpiresIn=expires_in,
    )