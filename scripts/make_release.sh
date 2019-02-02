#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

ORIGINAL_DIR=${PWD}

# Do not move this script from the scripts directory, it requires this and the relative path to website/
SCRIPTS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

git checkout release
git merge master
git diff-index --quiet HEAD
git commit || echo

${SCRIPTS_DIR}/build_static.sh

WEBSITE_DIR="${SCRIPTS_DIR}/../website"

rm -r $SCRIPTS_DIR/../static/
cp -R $WEBSITE_DIR/dist static/

git push heroku release:master

git checkout master
