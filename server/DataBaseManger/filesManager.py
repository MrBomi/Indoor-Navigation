import boto3
import os
from typing import Union, BinaryIO
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

ACCESS_KEY = os.getenv("R2_ACCESS_KEY_ID")
SECRET_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
ENDPOINT_URL = os.getenv("R2_ENDPOINT")
BUCKET_NAME = os.getenv("R2_BUCKET")

s3_client = boto3.client(
    "s3",
    endpoint_url=ENDPOINT_URL,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
)

def upload_to_r2(object_data: Union[bytes, BinaryIO], object_name: str, content_type: str = "application/octet-stream") -> str:
    """
    Upload an object to Cloudflare R2.

    :param object_data: The object to upload, as bytes or a file-like stream (e.g. BytesIO, request.files["file"].stream).
    :param object_name: The key (name) under which the object will be stored in the bucket.
    :param content_type: MIME type of the object (default is "application/octet-stream").
    :return: The key of the uploaded object in R2.
    """
    try:
        if isinstance(object_data, bytes):
            # Upload directly from bytes
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=object_name,
                Body=object_data,
                ContentType=content_type
            )
        else:
            # Upload from stream
            s3_client.upload_fileobj(
                Fileobj=object_data,
                Bucket=BUCKET_NAME,
                Key=object_name,
                ExtraArgs={"ContentType": content_type}
            )

        print(f"✅ Object '{object_name}' uploaded to bucket '{BUCKET_NAME}'")
        return object_name
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        raise

def download_from_r2(key: str) -> bytes:
    """
    Download an object from Cloudflare R2 and return its raw bytes.

    :param key: The object key (path/name) in the bucket.
    :return: Raw file content as bytes.
    :raises FileNotFoundError: If the object does not exist.
    :raises Exception: For any other error.
    """
    try:
        resp = s3_client.get_object(Bucket=BUCKET_NAME, Key=key)
        return resp["Body"].read()
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if code in {"NoSuchKey", "404"}:
            raise FileNotFoundError(f"Object not found: s3://{BUCKET_NAME}/{key}") from e
        raise

