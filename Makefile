# Development shell - access bash in the web container
bash:
	docker compose run --rm web bash

# Frontend asset management
npm-install: # Install npm dependencies
	npm install

npm-build: # Build frontend assets
	npm run build

# Docker management
pull: # Pull latest Docker images
	docker compose pull

image: # Build Docker image
	docker compose build --pull

# Complete build process including frontend and Docker
build: npm-install npm-build image

# Cleanup resources
clean: stop
	docker compose rm -f
	find . -name "*.pyc" -delete
	rm -rf jazzband/static/dist

# Database management
db-migrate: # Generate database migrations
	docker compose run --rm web flask db migrate

db-upgrade: # Apply database migrations
	docker compose run --rm web flask db upgrade

# Redis CLI access
redis-cli:
	docker compose run --rm redis redis-cli -h redis

# Application management
run: # Run application in foreground
	docker compose up

shell: # Run Flask shell for REPL interaction
	docker compose run --rm web flask shell

start: # Start application in background
	docker compose up -d

stop: # Stop application
	docker compose stop

# Dependency management
compile-update: # Update dependencies and compile requirements.txt
	docker compose run --rm web pip-compile -U --allow-unsafe --generate-hashes

update: # Install dependencies from requirements.txt
	docker compose run --rm web pip install -r requirements.txt

# Testing
pytest: # Run pytest
	docker compose run --rm web pytest tests/

test: pytest # Alias for pytest

lint: # Run linters
	docker compose run --rm web ruff check

format: # Format code with ruff
	docker compose run --rm web ruff format

# Environment setup
envvar: # Create .env file from template
	cp .env-dist .env

# CI/CD
ci: envvar test

# Security
generate-securitytxt: # Generate security.txt with GPG signature
	rm jazzband/static/security.txt
	gpg --clearsign -u 02DE8F842900411ADD70B1374D87558AF652A00F -o jazzband/static/security.txt jazzband/static/security.txt.tpl

verify-securitytxt: # Verify security.txt signature
	gpg --verify jazzband/static/security.txt

.PHONY: $(MAKECMDGOALS)
