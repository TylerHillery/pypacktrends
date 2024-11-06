#!/bin/bash

# Check if required arguments are provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <CONTAINER_REGISTRY_PREFIX> <SERVICE_NAME>"
    echo "Example: $0 ghcr.io/tylerhillery/pypacktrends/ backend"
    exit 1
fi

# Arguments
CONTAINER_REGISTRY_PREFIX=$1
SERVICE_NAME=$2
FULL_IMAGE_NAME="${CONTAINER_REGISTRY_PREFIX}${SERVICE_NAME}:latest"
LOG_FILE="/var/log/update_service_${SERVICE_NAME}.log"

# Logging function
log() {
    local message="$1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$SERVICE_NAME] $message" | tee -a "$LOG_FILE"
}

log "Starting update for service $SERVICE_NAME..."

# Pull the latest image for the specified service
log "Pulling the latest image: ${FULL_IMAGE_NAME}"
docker pull "$FULL_IMAGE_NAME"

# Get the list of dangling images for the specified service
dangling_image=$(docker images --filter "dangling=true" --filter "reference=${CONTAINER_REGISTRY_PREFIX}${SERVICE_NAME}" --format "{{.ID}}")

if [ -n "$dangling_image" ]; then
    log "Dangling image ID found: $dangling_image"
else
    log "No dangling images found. Exiting."
    exit 1
fi

# Get the container name attached to the dangling image
old_container=$(docker ps --filter "ancestor=$dangling_image" --format "{{.Names}}")

if [ -n "$old_container" ]; then
    log "Old container found: $old_container"
else
    log "No containers found for dangling image. Exiting."
    exit 1
fi

# Scale up the specified service to two containers
log "Scaling up service $SERVICE_NAME to two containers..."
docker compose -f docker-compose.yml up -d --no-deps --scale "$SERVICE_NAME"=2 --no-recreate "$SERVICE_NAME"

# Get the name of the new container for the specified service
new_container=$(docker ps --filter "ancestor=${FULL_IMAGE_NAME}" --format "{{.Names}}" | grep "$SERVICE_NAME" | tail -n 1)

if [ -n "$new_container" ]; then
    log "New container for service $SERVICE_NAME: $new_container"
else
    log "Failed to identify new container for service $SERVICE_NAME. Exiting."
    exit 1
fi

# Retrieve the Caddy container name (static name as specified in Docker Compose)
caddy_container="caddy"

# Check if the Caddy container is running
if docker ps --filter "name=^${caddy_container}$" --format "{{.Names}}" | grep -q "^${caddy_container}$"; then
    log "Caddy container found: $caddy_container"
else
    log "Caddy container not running or not found. Exiting."
    exit 1
fi

# Update Caddy with the new container name
log "Updating Caddy with the new container name for service $SERVICE_NAME..."
CONTAINER_NAME=$(echo "${SERVICE_NAME}" | tr '[:lower:]' '[:upper:]')_CONTAINER_NAME
docker exec -it "$caddy_container" /bin/sh -c "export ${CONTAINER_NAME}=$new_container && caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile"

# Remove the old container using the dangling image
log "Removing old container: $old_container..."
docker container rm -f "$old_container"

# 10: Remove the dangling image
log "Removing dangling image: $dangling_image..."
docker rmi "$dangling_image"

log "Update for service $SERVICE_NAME complete!"
