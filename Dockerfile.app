# Application image that uses the cached base image
ARG BASE_IMAGE
FROM node AS npm

WORKDIR /tmp

# Copy package files (should already be cached in base image)
COPY package.json package-lock.json /tmp/

# Install dependencies (this layer should be cached from base image build)
RUN npm update -g npm && npm install

# Copy application code and build frontend assets
COPY . /tmp/
RUN npm run build

# -----------------------------------------------------------------------------
# Use the cached base image
FROM ${BASE_IMAGE}

# Switch to root temporarily to copy files
USER root

# Copy application code
COPY . /app/

# Copy built frontend assets from the npm stage
COPY --from=npm /tmp/jazzband/static/dist /app/jazzband/static/dist/

# Ensure proper ownership
RUN chown -R 10001:10001 /app

# Switch back to app user
USER 10001

EXPOSE 5000

ENTRYPOINT ["/app/docker-entrypoint.sh", "--"]
