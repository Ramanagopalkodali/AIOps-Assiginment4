"""One-time download, then save a self-contained model for offline CPU inference."""
import json
from pathlib import Path
from transformers import BlipForConditionalGeneration, BlipProcessor

root = Path(__file__).resolve().parents[1]
destination = root / 'models' / 'blip-base'
destination.mkdir(parents=True, exist_ok=True)
name = 'Salesforce/blip-image-captioning-base'
print('Downloading the BLIP base model. Internet is needed for this setup step only.')
processor = BlipProcessor.from_pretrained(name, use_fast=False)
model = BlipForConditionalGeneration.from_pretrained(name)
revision = getattr(model.config, '_commit_hash', None)
processor.save_pretrained(destination)
model.save_pretrained(destination, safe_serialization=True)
(destination / 'source.json').write_text(json.dumps({'model': name, 'resolved_revision': revision}, indent=2))
print('Saved:', destination)
