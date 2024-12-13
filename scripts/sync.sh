#!/usr/bin/env bash

set -e

START_WEEK=$1
END_WEEK=$2

BACKEND_IMAGE="ghcr.io/tylerhillery/pypacktrends/backend:latest"
REMOTE_CREDS_PATH="/tmp/google-credentials.json"

backend_container=$(docker ps --filter "ancestor=${BACKEND_IMAGE}" --format "{{.Names}}" | grep "backend" | tail -n 1)

if [ -z "$backend_container" ]; then
    echo "Error: No running backend container found for image ${BACKEND_IMAGE}"
    exit 1
fi

echo "Using container: $backend_container"

docker cp ${REMOTE_CREDS_PATH} $backend_container:${REMOTE_CREDS_PATH}
docker exec \
    -e GOOGLE_APPLICATION_CREDENTIALS=${REMOTE_CREDS_PATH} \
    -e GOOGLE_CLOUD_PROJECT=pypacktrends-prod \
    $backend_container python /app/app/sync.py packages

docker exec \
    -e GOOGLE_APPLICATION_CREDENTIALS=${REMOTE_CREDS_PATH} \
    -e GOOGLE_CLOUD_PROJECT=pypacktrends-prod \
    $backend_container python /app/app/sync.py downloads ${START_WEEK} ${END_WEEK}
