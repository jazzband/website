# Common variables
DOCKER_RUN = docker compose run --rm
RUFF_DOCKER = docker run --rm -v $(PWD):/app -w /app ghcr.io/astral-sh/ruff:0.11.12

# Development shell - access bash in the web container
bash:
	$(DOCKER_RUN) web bash

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
	$(DOCKER_RUN) web flask db migrate

db-upgrade: # Apply database migrations
	$(DOCKER_RUN) web flask db upgrade

# Redis CLI access
redis-cli:
	$(DOCKER_RUN) redis redis-cli -h redis

# Application management
run: # Run application in foreground
	docker compose up

pull: # Pull Docker images
	docker compose pull

image: # Build Docker image
	docker compose build

shell: # Run Flask shell for REPL interaction
	$(DOCKER_RUN) web flask shell

start: # Start application in background
	docker compose up -d

stop: # Stop application
	docker compose stop

# Dependency management
compile-update: # Update dependencies and compile requirements.txt
	$(DOCKER_RUN) web pip-compile -U --allow-unsafe --generate-hashes

update: # Install dependencies from requirements.txt
	$(DOCKER_RUN) web pip install -r requirements.txt

# Testing
test: # Run tests (accepts optional environment variables via make target)
	$(DOCKER_RUN) $(TEST_ENV) web pytest tests/

lint: # Run linters using the official Ruff Docker image
	$(RUFF_DOCKER) check

format: # Format code using the official Ruff Docker image
	$(RUFF_DOCKER) format

# Environment setup
envvar: # Create .env file from template
	cp .env-dist .env

# CI/CD
ci: envvar # Run CI tasks (environment setup and tests)
	$(MAKE) test TEST_ENV="-e COVERAGE_FILE -e COVERAGE_XML -v /tmp/coverage:/tmp/coverage"

# Security
generate-securitytxt: # Generate security.txt with GPG signature
	rm jazzband/static/security.txt
	gpg --clearsign -u 02DE8F842900411ADD70B1374D87558AF652A00F -o jazzband/static/security.txt jazzband/static/security.txt.tpl

verify-securitytxt: # Verify security.txt signature
	gpg --verify jazzband/static/security.txt

.PHONY: $(MAKECMDGOALS)
