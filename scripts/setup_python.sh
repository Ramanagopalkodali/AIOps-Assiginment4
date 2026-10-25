#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
case "$(uname -m)" in
  x86_64) python -m pip install torch==2.9.0 --index-url https://download.pytorch.org/whl/cpu ;;
  aarch64|arm64) python -m pip install torch==2.9.0 ;;
  *) echo 'Expected a 64-bit x86_64 or aarch64 Ubuntu guest.'; exit 1 ;;
esac
python -m pip install -r requirements.txt
python -m pip check
python -m pip freeze > requirements-installed.txt
python -c 'import torch; print("Torch:", torch.__version__, "CUDA available:", torch.cuda.is_available())'
