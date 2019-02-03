#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

gunicorn --log-level info --worker-class eventlet -w 1 server:app
