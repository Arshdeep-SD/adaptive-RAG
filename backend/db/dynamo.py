from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger(__name__)


def _to_decimal(obj):
    """Recursively convert floats to Decimal for DynamoDB compatibility."""
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: _to_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_decimal(v) for v in obj]
    return obj


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dynamo_resource(table_name: str, region: str, endpoint_url: str | None):
    kwargs: dict = {"region_name": region}
    if endpoint_url:
        kwargs["endpoint_url"] = endpoint_url
    dynamo = boto3.resource("dynamodb", **kwargs)
    return dynamo.Table(table_name)


class DynamoJobStore:
    def __init__(self, table_name: str, region: str, endpoint_url: str | None = None):
        self._table = _dynamo_resource(table_name, region, endpoint_url)

    async def create(self, job: dict) -> None:
        self._table.put_item(Item=job, ConditionExpression="attribute_not_exists(job_id)")

    async def get(self, job_id: str) -> dict | None:
        resp = self._table.get_item(Key={"job_id": job_id})
        return resp.get("Item")

    async def update(self, job_id: str, **fields) -> None:
        if not fields:
            return
        exprs = []
        names: dict = {}
        values: dict = {}
        for k, v in fields.items():
            safe = f"#f_{k}"
            names[safe] = k
            values[f":v_{k}"] = v
            exprs.append(f"{safe} = :v_{k}")
        self._table.update_item(
            Key={"job_id": job_id},
            UpdateExpression="SET " + ", ".join(exprs),
            ExpressionAttributeNames=names,
            ExpressionAttributeValues=values,
        )

    async def update_status(self, job_id: str, status: str) -> None:
        await self.update(job_id, status=status)

    async def list_all(self) -> list[dict]:
        resp = self._table.scan()
        items = resp.get("Items", [])
        return sorted(items, key=lambda j: j.get("created_at", ""), reverse=True)

    async def delete(self, job_id: str) -> None:
        self._table.delete_item(Key={"job_id": job_id})


class DynamoRecordStore:
    def __init__(self, table_name: str, region: str, endpoint_url: str | None = None):
        self._table = _dynamo_resource(table_name, region, endpoint_url)

    async def put(self, record: dict) -> None:
        self._table.put_item(Item=record)

    async def get(self, record_id: str) -> dict | None:
        resp = self._table.get_item(Key={"record_id": record_id})
        return resp.get("Item")

    async def list_by_job(self, job_id: str) -> list[dict]:
        resp = self._table.query(
            IndexName="job_id-index",
            KeyConditionExpression=Key("job_id").eq(job_id),
        )
        return resp.get("Items", [])

    async def bulk_put(self, records: list[dict]) -> None:
        with self._table.batch_writer() as batch:
            for r in records:
                batch.put_item(Item=_to_decimal(r))

    async def delete_by_job(self, job_id: str) -> None:
        items = self._table.query(
            IndexName="job_id-index",
            KeyConditionExpression=Key("job_id").eq(job_id),
        ).get("Items", [])
        with self._table.batch_writer() as batch:
            for item in items:
                batch.delete_item(Key={"record_id": item["record_id"]})


class DynamoUserStore:
    def __init__(self, table_name: str, region: str, endpoint_url: str | None = None):
        self._table = _dynamo_resource(table_name, region, endpoint_url)

    async def create(self, user: dict) -> None:
        self._table.put_item(Item=user, ConditionExpression="attribute_not_exists(user_id)")

    async def get_by_username(self, username: str) -> dict | None:
        resp = self._table.query(
            IndexName="username-index",
            KeyConditionExpression=Key("username").eq(username),
        )
        items = resp.get("Items", [])
        return items[0] if items else None

    async def get_by_id(self, user_id: str) -> dict | None:
        resp = self._table.get_item(Key={"user_id": user_id})
        return resp.get("Item")

    async def list_all(self) -> list[dict]:
        resp = self._table.scan()
        items = resp.get("Items", [])
        return sorted(items, key=lambda u: u.get("created_at", ""))

    async def delete(self, user_id: str) -> None:
        self._table.delete_item(Key={"user_id": user_id})


class DynamoUICacheStore:
    def __init__(self, table_name: str, region: str, endpoint_url: str | None = None):
        self._table = _dynamo_resource(table_name, region, endpoint_url)

    async def get(self, pattern_hash: str) -> dict | None:
        resp = self._table.get_item(Key={"query_pattern_hash": pattern_hash})
        return resp.get("Item")

    async def put(self, pattern_hash: str, ui_schema: dict, sample_query: str = "") -> None:
        self._table.put_item(Item=_to_decimal({
            "query_pattern_hash": pattern_hash,
            "ui_schema": ui_schema,
            "hit_count": 0,
            "last_used_at": _now_iso(),
            "sample_query": sample_query,
        }))

    async def increment_hit(self, pattern_hash: str) -> None:
        self._table.update_item(
            Key={"query_pattern_hash": pattern_hash},
            UpdateExpression="SET hit_count = hit_count + :one, last_used_at = :ts",
            ExpressionAttributeValues={":one": 1, ":ts": _now_iso()},
        )
