# Makefile for Atrean RAG Platform

.PHONY: help build up down logs clean test load-data

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build Docker images
	docker-compose build

up: ## Start all services
	docker-compose up -d

down: ## Stop all services
	docker-compose down

logs: ## Show logs for all services
	docker-compose logs -f

logs-app: ## Show logs for app service
	docker-compose logs -f app

logs-db: ## Show logs for database service
	docker-compose logs -f postgres

clean: ## Clean up containers and volumes
	docker-compose down -v
	docker system prune -f

test: ## Run tests
	docker-compose exec app python -m pytest

load-data: ## Load dataset into database
	docker-compose exec app python scripts/load_dataset.py

shell: ## Open shell in app container
	docker-compose exec app bash

db-shell: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U atx -d atx_db

restart: ## Restart all services
	docker-compose restart

status: ## Show status of all services
	docker-compose ps
