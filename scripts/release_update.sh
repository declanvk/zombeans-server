#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

ORIGINAL_DIR=${PWD}

# Do not move this script from the scripts directory, it requires this and the relative path to website/
SCRIPTS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

WEBSITE_DIR="${SCRIPTS_DIR}/../website"

# Move into release for all dirty work
git checkout release

# Get the latest changes in master
git merge master

# And check that they merged cleanly
git diff-index --quiet HEAD

# If it needs a commit, add and echo to catch if no release is needed
git commit -m "Update server" || echo

# Build static resources and move into
${SCRIPTS_DIR}/build_static.sh
rm -r $SCRIPTS_DIR/../static/
cp -R $WEBSITE_DIR/dist static/

# Add all changes to static
git add static

# If it needs a commit, add and echo to catch if no release is needed
git commit -m "Update static resources" || echo

# Perform last check for cleanliness
git status --porcelain

# If we get to this point, release is on the point of both server and web master
git push heroku release:master

git checkout master

