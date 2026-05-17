from __future__ import annotations

import boto3


class S3FileStore:
    """AWS S3 object store."""

    def __init__(self, bucket: str, region: str = "us-west-2", endpoint_url: str | None = None):
        self._bucket = bucket
        self._client = boto3.client(
            "s3",
            region_name=region,
            endpoint_url=endpoint_url,
        )

    async def put(self, key: str, data: bytes) -> None:
        self._client.put_object(Bucket=self._bucket, Key=key, Body=data)

    async def get(self, key: str) -> bytes:
        resp = self._client.get_object(Bucket=self._bucket, Key=key)
        return resp["Body"].read()

    async def list_keys(self, prefix: str) -> list[str]:
        paginator = self._client.get_paginator("list_objects_v2")
        keys = []
        for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                keys.append(obj["Key"])
        return sorted(keys)

    async def delete_prefix(self, prefix: str) -> None:
        keys = await self.list_keys(prefix)
        if keys:
            self._client.delete_objects(
                Bucket=self._bucket,
                Delete={"Objects": [{"Key": k} for k in keys]},
            )

    async def get_prefix(self, prefix: str) -> list[tuple[str, bytes]]:
        paginator = self._client.get_paginator("list_objects_v2")
        results = []
        for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                data = await self.get(obj["Key"])
                results.append((obj["Key"], data))
        return results
