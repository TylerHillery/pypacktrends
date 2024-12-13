#!/usr/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "Error: .env file not found in project root"
    exit 1
fi

mkdir -p "$PROJECT_ROOT/data"

env $(cat "$PROJECT_ROOT/.env") litestream restore \
    -config "$PROJECT_ROOT/litestream/litestream.yml" \
    -o "$PROJECT_ROOT/data/pypacktrends.db" \
    /data/pypacktrends.db

if [ $? -eq 0 ]; then
    echo "Database successfully restored to $PROJECT_ROOT/data/pypacktrends.db"
else
    echo "Error: Database restore failed"
    exit 1
fi
