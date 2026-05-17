FROM public.ecr.aws/lambda/python:3.12

WORKDIR /var/task

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download SentenceTransformer model weights to avoid cold-start downloads
# Only applies when EMBEDDING_PROVIDER=local; skip for bedrock-only deploys
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')" || true

COPY . .

CMD ["lambda_handlers.ingest_worker_handler.handler"]
