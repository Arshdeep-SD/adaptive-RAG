from __future__ import annotations

import logging
import os
import secrets
from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- local vs AWS toggle ---
    USE_LOCAL_STORE: bool = True

    # --- embedding ---
    EMBEDDING_PROVIDER: Literal["local", "bedrock"] = "local"

    # --- AWS ---
    AWS_REGION: str = "us-west-2"
    AWS_ACCESS_KEY_ID: str = "test"
    AWS_SECRET_ACCESS_KEY: str = "test"

    # --- DynamoDB (set endpoint for LocalStack) ---
    DYNAMO_ENDPOINT: str | None = None
    JOBS_TABLE: str = "Jobs"
    RECORDS_TABLE: str = "Records"
    UI_CACHE_TABLE: str = "UICache"

    # --- S3 ---
    S3_ENDPOINT: str | None = None
    S3_BUCKET: str = "adaptive-rag-dev"

    # --- OpenSearch ---
    OPENSEARCH_ENDPOINT: str | None = None
    OPENSEARCH_INDEX: str = "records-v1-local"

    # --- local storage ---
    LOCAL_STORAGE_PATH: str = "/tmp/adaptive-rag"

    # --- Ollama (local open-source LLM, no API key required) ---
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    OLLAMA_VISION_MODEL: str = "llava"

    # --- Bedrock ---
    BEDROCK_REGION: str = "us-west-2"
    BEDROCK_ANSWER_MODEL: str = "us.meta.llama3-3-70b-instruct-v1:0"
    BEDROCK_VISION_MODEL: str = "us.meta.llama4-maverick-17b-instruct-v1:0"
    BEDROCK_EMBEDDING_MODEL: str = "amazon.titan-embed-text-v2:0"

    # --- Auth / JWT ---
    JWT_SECRET: str = ""
    JWT_EXPIRE_HOURS: int = 24
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "changeme"
    USERS_TABLE: str = "Users"

    @model_validator(mode="after")
    def _warn_insecure_defaults(self) -> "Settings":
        if not self.JWT_SECRET:
            self.JWT_SECRET = secrets.token_hex(32)
            logger.warning(
                "JWT_SECRET not set — generated a random secret. "
                "Tokens will be invalidated on every restart. Set JWT_SECRET in .env for persistence."
            )
        if self.ADMIN_PASSWORD == "changeme":
            logger.warning(
                "ADMIN_PASSWORD is set to the default 'changeme'. "
                "Set ADMIN_PASSWORD in .env before deploying."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
