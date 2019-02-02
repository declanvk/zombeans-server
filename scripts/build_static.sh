#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

ORIGINAL_DIR=${PWD}

# Do not move this script from the scripts directory, it requires this and the relative path to website/
SCRIPTS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

WEBSITE_DIR="${SCRIPTS_DIR}/../website"

cd $WEBSITE_DIR

npm install
npm run build

# Now in main server directory
cd ..

export ZOMBIES_STATIC_FOLDER="${PWD}/website/dist"

cd $ORIGINAL_DIR
