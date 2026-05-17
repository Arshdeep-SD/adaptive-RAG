from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class OpenSearchVectorStore:
    """AWS OpenSearch Serverless vector store using k-NN search."""

    def __init__(self, endpoint: str, index: str = "records-v1"):
        from opensearchpy import OpenSearch, RequestsHttpConnection
        from requests_aws4auth import AWS4Auth
        import boto3

        region = endpoint.split(".")[1] if "." in endpoint else "us-west-2"
        credentials = boto3.Session().get_credentials()
        auth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            region,
            "aoss",
            session_token=credentials.token,
        )
        host = endpoint.replace("https://", "").replace("http://", "")
        self._client = OpenSearch(
            hosts=[{"host": host, "port": 443}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
        )
        self._index = index

    def ensure_index(self, dim: int) -> None:
        """Create index with knn_vector mapping if it doesn't exist."""
        if self._client.indices.exists(index=self._index):
            return
        self._client.indices.create(
            index=self._index,
            body={
                "settings": {"index": {"knn": True}},
                "mappings": {
                    "properties": {
                        "record_id": {"type": "keyword"},
                        "job_id": {"type": "keyword"},
                        "text": {"type": "text"},
                        "embedding": {
                            "type": "knn_vector",
                            "dimension": dim,
                            "method": {
                                "name": "hnsw",
                                "space_type": "cosinesimil",
                                "engine": "faiss",
                            },
                        },
                    }
                },
            },
        )
        logger.info("Created OpenSearch index %s (dim=%d)", self._index, dim)

    async def bulk_index(self, records: list[dict]) -> None:
        if not records:
            return
        dim = len(records[0]["embedding"])
        self.ensure_index(dim)

        actions = []
        for r in records:
            actions.append({"index": {"_index": self._index}})
            actions.append({
                "record_id": r["record_id"],
                "job_id": r.get("job_id", ""),
                "text": r["text"],
                "embedding": r["embedding"],
            })
        resp = self._client.bulk(body=actions)
        if resp.get("errors"):
            failed = [i["index"]["error"] for i in resp["items"] if i.get("index", {}).get("error")]
            logger.error("Bulk index had %d failures: %s", len(failed), failed[:2])

    async def count_by_job(self, job_id: str) -> int:
        if not self._client.indices.exists(index=self._index):
            return 0
        resp = self._client.count(
            index=self._index,
            body={"query": {"term": {"job_id": job_id}}},
        )
        return resp.get("count", 0)

    async def delete_by_job(self, job_id: str) -> None:
        if not self._client.indices.exists(index=self._index):
            return
        self._client.delete_by_query(
            index=self._index,
            body={"query": {"term": {"job_id": job_id}}},
        )

    async def search(
        self, embedding: list[float], top_k: int, allowed_job_ids: set[str] | None = None
    ) -> list[dict]:
        knn_clause: dict = {"vector": embedding, "k": top_k}
        if allowed_job_ids is not None:
            # Pre-filter inside the knn clause so OpenSearch never scores or
            # returns vectors from excluded jobs. Without this, ghost vectors
            # (from deleted jobs) fill the top-k window and crowd out live data.
            knn_clause["filter"] = {"terms": {"job_id": list(allowed_job_ids)}}

        resp = self._client.search(
            index=self._index,
            body={
                "size": top_k,
                "query": {"knn": {"embedding": knn_clause}},
                "_source": ["record_id"],
            },
        )
        return [
            {"record_id": hit["_source"]["record_id"], "score": hit["_score"]}
            for hit in resp["hits"]["hits"]
        ]
