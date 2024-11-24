#!/usr/bin/env bash

set -x
set -e

script_dir=$(dirname "$0")

uv run sqlfluff fix $script_dir/..
uv run sqlfluff lint $script_dir/..
