#!/bin/bash
script_dir=$(dirname "$0")
sqlfluff lint $script_dir/..
sqlfluff fix $script_dir/..
