#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

printf "Cleaning submodules\n"
git submodule foreach git clean -df

printf "Updating submodules\n"
git submodule update --recursive --remote
