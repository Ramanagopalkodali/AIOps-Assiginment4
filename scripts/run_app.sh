#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"
exec python -m streamlit run "$A4_ROOT/src/caption_app/ui.py" --server.address 127.0.0.1 --server.port 8501 --server.maxUploadSize 100 --browser.gatherUsageStats false
