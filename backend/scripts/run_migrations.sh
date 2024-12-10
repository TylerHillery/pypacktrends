#!/usr/bin/env bash

set -e

# Get the directory where the script is located
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")

# Change to the parent directory of the script
cd "$SCRIPT_DIR/.."

alembic upgrade head
