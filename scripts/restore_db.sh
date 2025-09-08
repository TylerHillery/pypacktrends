#!/usr/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "Error: .env file not found in project root"
    exit 1
fi

mkdir -p "$PROJECT_ROOT/data"

docker run --rm \
  --env-file "$PROJECT_ROOT/.env" \
  -v "$PROJECT_ROOT/data:/data" \
  -v "$PROJECT_ROOT/litestream/litestream.yml:/etc/litestream.yml" \
  litestream/litestream restore -if-replica-exists \
  -o /data/pypacktrends.db /data/pypacktrends.db

if [ $? -eq 0 ]; then
    echo "Database successfully restored to $PROJECT_ROOT/data/pypacktrends.db"
else
    echo "Error: Database restore failed"
    exit 1
fi
