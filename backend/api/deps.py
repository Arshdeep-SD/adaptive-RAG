from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from backend.core.config import Settings, get_settings
from backend.db.local_store import (
    LocalJobStore,
    LocalRecordStore,
    LocalUICacheStore,
    LocalVectorStore,
)


# ---------------------------------------------------------------------------
# Singletons — one instance for the lifetime of the process
# ---------------------------------------------------------------------------

@lru_cache
def _local_job_store() -> LocalJobStore:
    return LocalJobStore()


@lru_cache
def _local_record_store() -> LocalRecordStore:
    return LocalRecordStore()


@lru_cache
def _local_ui_cache_store() -> LocalUICacheStore:
    return LocalUICacheStore()


@lru_cache
def _local_vector_store() -> LocalVectorStore:
    return LocalVectorStore()


# ---------------------------------------------------------------------------
# Dependency providers — swap implementations here when USE_LOCAL_STORE=False
# ---------------------------------------------------------------------------

def get_job_store(settings: Annotated[Settings, Depends(get_settings)]):
    if settings.USE_LOCAL_STORE:
        return _local_job_store()
    from backend.db.dynamo import DynamoJobStore
    return DynamoJobStore(
        table_name=settings.JOBS_TABLE,
        region=settings.AWS_REGION,
        endpoint_url=settings.DYNAMO_ENDPOINT,
    )


def get_record_store(settings: Annotated[Settings, Depends(get_settings)]):
    if settings.USE_LOCAL_STORE:
        return _local_record_store()
    from backend.db.dynamo import DynamoRecordStore
    return DynamoRecordStore(
        table_name=settings.RECORDS_TABLE,
        region=settings.AWS_REGION,
        endpoint_url=settings.DYNAMO_ENDPOINT,
    )


def get_ui_cache_store(settings: Annotated[Settings, Depends(get_settings)]):
    if settings.USE_LOCAL_STORE:
        return _local_ui_cache_store()
    from backend.db.dynamo import DynamoUICacheStore
    return DynamoUICacheStore(
        table_name=settings.UI_CACHE_TABLE,
        region=settings.AWS_REGION,
        endpoint_url=settings.DYNAMO_ENDPOINT,
    )


def get_vector_store(settings: Annotated[Settings, Depends(get_settings)]):
    if settings.USE_LOCAL_STORE:
        return _local_vector_store()
    from backend.search.opensearch import OpenSearchVectorStore
    return OpenSearchVectorStore(
        endpoint=settings.OPENSEARCH_ENDPOINT,
        index=settings.OPENSEARCH_INDEX,
    )


def get_object_store(settings: Annotated[Settings, Depends(get_settings)]):
    if settings.USE_LOCAL_STORE:
        from backend.storage.local_fs import LocalFileStore
        return LocalFileStore(settings.LOCAL_STORAGE_PATH)
    from backend.storage.s3 import S3FileStore
    return S3FileStore(
        bucket=settings.S3_BUCKET,
        region=settings.AWS_REGION,
        endpoint_url=settings.S3_ENDPOINT,
    )


def get_embedding_provider(settings: Annotated[Settings, Depends(get_settings)]):
    if settings.EMBEDDING_PROVIDER == "local":
        from backend.embedding.local_provider import LocalEmbeddingProvider
        return LocalEmbeddingProvider()
    from backend.embedding.bedrock_provider import BedrockEmbeddingProvider
    return BedrockEmbeddingProvider(region=settings.BEDROCK_REGION)


def get_user_store(settings: Annotated[Settings, Depends(get_settings)]):
    from backend.auth.store import _local_user_store
    if settings.USE_LOCAL_STORE:
        return _local_user_store()
    from backend.db.dynamo import DynamoUserStore  # noqa: F401 — AWS path stub
    return DynamoUserStore(
        table_name=settings.USERS_TABLE,
        region=settings.AWS_REGION,
        endpoint_url=settings.DYNAMO_ENDPOINT,
    )
