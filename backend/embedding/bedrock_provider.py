from __future__ import annotations

import json
import boto3


class BedrockEmbeddingProvider:
    """AWS Bedrock Titan Text Embeddings v2 (1024-dim)."""

    dim = 1024
    MODEL_ID = "amazon.titan-embed-text-v2:0"

    def __init__(self, region: str = "us-west-2"):
        self._client = boto3.client("bedrock-runtime", region_name=region)

    def embed(self, texts: list[str]) -> list[list[float]]:
        results: list[list[float]] = []
        for text in texts:
            resp = self._client.invoke_model(
                modelId=self.MODEL_ID,
                contentType="application/json",
                accept="application/json",
                body=json.dumps({"inputText": text}),
            )
            body = json.loads(resp["body"].read())
            results.append(body["embedding"])
        return results
