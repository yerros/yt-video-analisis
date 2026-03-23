.PHONY: help setup install install-frontend install-backend dev dev-all dev-frontend dev-backend dev-worker dev-redis stop restart migrate migrate-create clean format lint test

# Python virtual environment
VENV = backend/venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

help:
	@echo "Available commands:"
	@echo "  make setup           - Initial setup (create venv + install all dependencies)"
	@echo "  make install         - Install all dependencies (frontend + backend)"
	@echo "  make install-backend - Install backend dependencies only"
	@echo "  make install-frontend- Install frontend dependencies only"
	@echo "  make dev-all         - Run all services concurrently (Redis, Backend, Worker, Frontend)"
	@echo "  make dev             - Show instructions to run services separately"
	@echo "  make restart         - Kill all processes and restart all services (RECOMMENDED)"
	@echo "  make stop            - Stop all running services"
	@echo "  make dev-frontend    - Run frontend dev server"
	@echo "  make dev-backend     - Run backend API server"
	@echo "  make dev-worker      - Run Celery worker"
	@echo "  make dev-redis       - Run Redis server"
	@echo "  make migrate         - Run database migrations"
	@echo "  make migrate-create  - Create new migration"
	@echo "  make clean           - Clean temporary files"
	@echo "  make format          - Format code (black + prettier)"
	@echo "  make lint            - Lint code (ruff + eslint)"

setup: $(VENV)/bin/activate install
	@echo "Setup complete! Activate venv with: source backend/venv/bin/activate"

$(VENV)/bin/activate:
	@echo "Creating Python virtual environment..."
	python3 -m venv $(VENV)
	@echo "Virtual environment created!"

install: install-frontend install-backend

install-frontend:
	@echo "Installing frontend dependencies..."
	cd frontend && pnpm install
	@echo "Frontend dependencies installed!"

install-backend: $(VENV)/bin/activate
	@echo "Installing backend dependencies..."
	$(PIP) install -r backend/requirements.txt
	@echo "Backend dependencies installed!"

dev:
	@echo "To run all services in separate terminals:"
	@echo "  Terminal 1: make dev-redis"
	@echo "  Terminal 2: make dev-backend"
	@echo "  Terminal 3: make dev-worker"
	@echo "  Terminal 4: make dev-frontend"
	@echo ""
	@echo "Or run all services at once:"
	@echo "  make dev-all"

dev-all: $(VENV)/bin/activate
	@echo "Starting all services..."
	@echo "Press Ctrl+C to stop all services"
	@trap 'make stop' INT; \
	redis-server --daemonize yes && \
	$(VENV)/bin/uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 & \
	BACKEND_PID=$$!; \
	$(VENV)/bin/celery -A backend.celery_app worker --loglevel=info & \
	WORKER_PID=$$!; \
	cd frontend && pnpm dev & \
	FRONTEND_PID=$$!; \
	echo ""; \
	echo "=============================================="; \
	echo "All services started!"; \
	echo "=============================================="; \
	echo "Frontend:  http://localhost:3000"; \
	echo "Backend:   http://localhost:8000"; \
	echo "API Docs:  http://localhost:8000/docs"; \
	echo "=============================================="; \
	echo ""; \
	echo "Press Ctrl+C to stop all services..."; \
	wait $$BACKEND_PID $$WORKER_PID $$FRONTEND_PID

stop:
	@./stop.sh

restart:
	@./restart.sh

dev-frontend:
	cd frontend && pnpm dev

dev-backend: $(VENV)/bin/activate
	$(VENV)/bin/uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

dev-worker: $(VENV)/bin/activate
	$(VENV)/bin/celery -A backend.celery_app worker --loglevel=info

dev-redis:
	redis-server

migrate: $(VENV)/bin/activate
	$(VENV)/bin/alembic -c backend/alembic.ini upgrade head

migrate-create: $(VENV)/bin/activate
	@read -p "Enter migration message: " msg; \
	$(VENV)/bin/alembic -c backend/alembic.ini revision --autogenerate -m "$$msg"

clean:
	@echo "Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf frontend/.next
	rm -rf frontend/node_modules/.cache
	rm -rf backend/venv
	rm -rf /tmp/video-analysis/*
	@echo "Clean complete!"

format: $(VENV)/bin/activate
	@echo "Formatting Python code..."
	$(VENV)/bin/black backend && $(VENV)/bin/ruff check --fix backend
	@echo "Formatting TypeScript code..."
	cd frontend && pnpm format
	@echo "Format complete!"

lint: $(VENV)/bin/activate
	@echo "Linting Python code..."
	$(VENV)/bin/ruff check backend
	@echo "Linting TypeScript code..."
	cd frontend && pnpm lint
	@echo "Lint complete!"

test:
	@echo "Running tests..."
	@echo "Tests not implemented yet"
