# Common variables
DOCKER_RUN = docker compose run --rm
RUFF_DOCKER = docker run --rm -v $(PWD):/app -w /app ghcr.io/astral-sh/ruff:0.11.12

# Docker image variables
REGISTRY = ghcr.io
BASE_IMAGE_NAME = $(shell echo "$$(git config --get remote.origin.url | sed 's/.*github.com[:/]\([^.]*\).*/\1/')/base" | tr '[:upper:]' '[:lower:]')

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

# Docker caching tasks
build-base: # Build base image with current dependencies
	$(eval DEPS_HASH := $(shell cat requirements.txt package.json package-lock.json | sha256sum | cut -d' ' -f1))
	@echo "Building base image with dependencies hash: $(DEPS_HASH)"
	docker build -f Dockerfile.base \
		--build-arg DEPS_HASH=$(DEPS_HASH) \
		-t $(REGISTRY)/$(BASE_IMAGE_NAME):deps-$(DEPS_HASH) \
		-t $(REGISTRY)/$(BASE_IMAGE_NAME):latest \
		.

build-app: # Build application image using cached base
	$(eval DEPS_HASH := $(shell cat requirements.txt package.json package-lock.json | sha256sum | cut -d' ' -f1))
	$(eval BASE_IMG := $(if $(BASE_IMAGE),$(BASE_IMAGE),$(REGISTRY)/$(BASE_IMAGE_NAME):deps-$(DEPS_HASH)))
	@echo "Building app image using base: $(BASE_IMG)"
	docker build -f Dockerfile.app \
		--build-arg BASE_IMAGE=$(BASE_IMG) \
		-t jazzband-website:latest \
		.

check-base: # Check for cached base image
	$(eval DEPS_HASH := $(shell cat requirements.txt package.json package-lock.json | sha256sum | cut -d' ' -f1))
	@echo "Checking for base image with hash: $(DEPS_HASH)"
	@if ! docker image inspect $(REGISTRY)/$(BASE_IMAGE_NAME):deps-$(DEPS_HASH) >/dev/null 2>&1; then \
		echo "Base image not found locally, attempting to pull..."; \
		docker pull $(REGISTRY)/$(BASE_IMAGE_NAME):deps-$(DEPS_HASH) || \
		(echo "Base image not available, building locally..." && $(MAKE) build-base); \
	else \
		echo "Base image found locally"; \
	fi

# Complete build process including frontend and Docker
build: npm-install npm-build image

# Optimized build using cached base
build-cached: check-base build-app # Build with dependency caching

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
	$(MAKE) test TEST_ENV="-e COVERAGE_FILE -e COVERAGE_XML"

# Security
generate-securitytxt: # Generate security.txt with GPG signature
	rm jazzband/static/security.txt
	gpg --clearsign -u 02DE8F842900411ADD70B1374D87558AF652A00F -o jazzband/static/security.txt jazzband/static/security.txt.tpl

verify-securitytxt: # Verify security.txt signature
	gpg --verify jazzband/static/security.txt

.PHONY: $(MAKECMDGOALS)
