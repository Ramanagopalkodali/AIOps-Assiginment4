#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export CAPTION_THREADS="${CAPTION_THREADS:-2}"
exec python -m caption_app.backend
