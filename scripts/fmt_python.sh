#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

yapf -i --style pep8 -r .
