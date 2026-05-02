import asyncio
import logging
from datetime import datetime, timezone
from functools import partial

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class StorageClient:
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        secure: bool = False,
    ) -> None:
        scheme = "https" if secure else "http"
        self._client = boto3.client(
            "s3",
            endpoint_url=f"{scheme}://{endpoint}",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="us-east-1",  # MinIO ignores region but boto3 requires one
        )

    def _run(self, fn, *args, **kwargs):
        """Run a sync boto3 call in the default thread-pool executor."""
        loop = asyncio.get_running_loop()
        return loop.run_in_executor(None, partial(fn, *args, **kwargs))

    async def create_bucket_if_not_exists(self, bucket: str) -> None:
        try:
            await self._run(self._client.head_bucket, Bucket=bucket)
        except ClientError as exc:
            if exc.response["Error"]["Code"] in ("404", "NoSuchBucket"):
                await self._run(self._client.create_bucket, Bucket=bucket)
                logger.info("Created bucket: %s", bucket)
            else:
                raise

    async def upload(self, bucket: str, key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
        import io
        await self._run(
            self._client.upload_fileobj,
            io.BytesIO(data),
            bucket,
            key,
            ExtraArgs={"ContentType": content_type},
        )

    async def download(self, bucket: str, key: str) -> bytes:
        import io
        buf = io.BytesIO()
        await self._run(self._client.download_fileobj, bucket, key, buf)
        return buf.getvalue()

    async def delete(self, bucket: str, key: str) -> None:
        await self._run(self._client.delete_object, Bucket=bucket, Key=key)

    async def presigned_url(self, bucket: str, key: str, expires_seconds: int = 3600) -> str:
        url = await self._run(
            self._client.generate_presigned_url,
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_seconds,
        )
        return url

    async def object_exists(self, bucket: str, key: str) -> bool:
        try:
            await self._run(self._client.head_object, Bucket=bucket, Key=key)
            return True
        except ClientError:
            return False
