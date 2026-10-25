#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"
exec python "$A4_ROOT/scripts/alert_receiver.py"
