#!/usr/bin/env python3
"""
Bootstrap LocalStack: create DynamoDB tables + S3 bucket.
Run with: python scripts/bootstrap_local.py
"""
import boto3

ENDPOINT = "http://localhost:4566"
REGION = "us-west-2"


def boto_kwargs():
    return {
        "region_name": REGION,
        "endpoint_url": ENDPOINT,
        "aws_access_key_id": "test",
        "aws_secret_access_key": "test",
    }


def create_tables():
    dynamo = boto3.client("dynamodb", **boto_kwargs())
    existing = {t["TableName"] for t in dynamo.list_tables()["TableNames"]}

    tables = [
        {
            "TableName": "Jobs",
            "KeySchema": [{"AttributeName": "job_id", "KeyType": "HASH"}],
            "AttributeDefinitions": [{"AttributeName": "job_id", "AttributeType": "S"}],
            "BillingMode": "PAY_PER_REQUEST",
        },
        {
            "TableName": "Records",
            "KeySchema": [{"AttributeName": "record_id", "KeyType": "HASH"}],
            "AttributeDefinitions": [
                {"AttributeName": "record_id", "AttributeType": "S"},
                {"AttributeName": "job_id", "AttributeType": "S"},
            ],
            "BillingMode": "PAY_PER_REQUEST",
            "GlobalSecondaryIndexes": [
                {
                    "IndexName": "job_id-index",
                    "KeySchema": [{"AttributeName": "job_id", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
        },
        {
            "TableName": "UICache",
            "KeySchema": [{"AttributeName": "query_pattern_hash", "KeyType": "HASH"}],
            "AttributeDefinitions": [
                {"AttributeName": "query_pattern_hash", "AttributeType": "S"}
            ],
            "BillingMode": "PAY_PER_REQUEST",
        },
    ]

    for tdef in tables:
        name = tdef["TableName"]
        if name in existing:
            print(f"  Table {name} already exists, skipping")
            continue
        dynamo.create_table(**tdef)
        print(f"  Created table: {name}")


def create_bucket():
    s3 = boto3.client("s3", **boto_kwargs())
    try:
        s3.create_bucket(
            Bucket="adaptive-rag-dev",
            CreateBucketConfiguration={"LocationConstraint": REGION},
        )
        print("  Created bucket: adaptive-rag-dev")
    except s3.exceptions.BucketAlreadyOwnedByYou:
        print("  Bucket already exists, skipping")
    except Exception as e:
        print(f"  Bucket creation: {e}")


if __name__ == "__main__":
    print("Bootstrapping LocalStack...")
    create_tables()
    create_bucket()
    print("Done.")
