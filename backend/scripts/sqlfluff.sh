#!/usr/bin/env bash

set -x

script_dir=$(dirname "$0")

sqlfluff fix $script_dir/..
sqlfluff lint $script_dir/..
