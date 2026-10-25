"""Central project paths, independent of the shell's current working directory."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = ROOT / 'models' / 'blip-base'
EVIDENCE_DIR = ROOT / 'evidence'
