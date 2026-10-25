#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"
exec python -m unittest discover -s tests -t . -v
