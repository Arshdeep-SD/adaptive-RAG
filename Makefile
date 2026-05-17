.PHONY: dev stop test seed bootstrap-local deploy install-backend install-frontend

# --- Local development ---
dev:
	cp -n .env.example .env 2>/dev/null || true
	docker-compose up --build

stop:
	docker-compose down

# --- Install dependencies locally (without Docker) ---
install-backend:
	cd backend && pip install -r requirements-dev.txt

install-frontend:
	cd frontend && npm install

# --- Run tests ---
test-backend:
	cd backend && pytest tests/ -v

test-frontend:
	cd frontend && npm run test

test: test-backend test-frontend

# --- Bootstrap LocalStack (create tables + bucket) ---
bootstrap-local:
	python scripts/bootstrap_local.py

# --- Seed demo data ---
seed:
	python scripts/seed_demo.py

# --- AWS CDK deployment ---
deploy:
	cd infra && npm install && npx cdk deploy --require-approval never

# --- Dev without Docker (local Python + Vite) ---
dev-local:
	@echo "Starting FastAPI on :8000..."
	cd backend && USE_LOCAL_STORE=true EMBEDDING_PROVIDER=local uvicorn backend.api.main:app --reload --port 8000 &
	@echo "Starting Vite on :5173..."
	cd frontend && npm run dev
