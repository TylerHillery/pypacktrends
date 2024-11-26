#!/usr/bin/env bash

set -x
set -e

script_dir=$(dirname "$0")

sqlfluff fix $script_dir/..
sqlfluff lint $script_dir/..
