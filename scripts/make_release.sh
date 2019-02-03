#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

ORIGINAL_DIR=${PWD}

# Do not move this script from the scripts directory, it requires this and the relative path to website/
SCRIPTS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

WEBSITE_DIR="${SCRIPTS_DIR}/../website"

# Move into release brnach to perofm all work that will never leave
git checkout release

# Checkout latest master to see if anything has changed recently
git merge master

# Check if anything is out of place in repo
git diff-index --quiet HEAD
git status --porcelain

# Build static to check if they have changed since last release
${SCRIPTS_DIR}/build_static.sh
rm -r $SCRIPTS_DIR/../static/
cp -R $WEBSITE_DIR/dist static/

# Check if anything is out of place in repo
git diff-index --quiet HEAD
git status --porcelain

# If we get to this point, release is on the point of both server and web master
git push heroku release:master

# Go back
git checkout master
