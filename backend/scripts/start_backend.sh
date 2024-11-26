#!/usr/bin/env bash

set -e
set -x

# Get the directory where the script is located
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
PROJECT_ROOT=$(realpath "$SCRIPT_DIR/..")

cd "$PROJECT_ROOT"

"$SCRIPT_DIR/run_migrations.sh"

# Check the ENVIRONMENT variable
if [ "${ENVIRONMENT}" = "dev" ]; then
    exec fastapi run --reload app/main.py
else
    exec fastapi run --workers 4 app/main.py
fi
