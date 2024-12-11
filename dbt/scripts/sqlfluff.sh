#!/usr/bin/env bash

script_dir=$(dirname "$0")

sqlfluff fix $script_dir/..
sqlfluff lint $script_dir/..
