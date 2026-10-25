#!/usr/bin/env bash
# Source from launch scripts; computes root before changing the working directory.
set -euo pipefail
A4_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$A4_ROOT"
if [[ "${CONDA_DEFAULT_ENV:-}" == "aiops" ]]; then
    :
elif [[ -f "$A4_ROOT/.venv/bin/activate" ]]; then
    source "$A4_ROOT/.venv/bin/activate"
else
    echo 'Activate your environment first: conda activate aiops'
    exit 1
fi
export PYTHONPATH="$A4_ROOT/src:$A4_ROOT${PYTHONPATH:+:$PYTHONPATH}"
