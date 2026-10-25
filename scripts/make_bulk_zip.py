"""Create an actual workload from your own photos, never fabricated results."""
import argparse
import zipfile
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('folder', type=Path)
parser.add_argument('output', type=Path)
parser.add_argument('--copies', type=int, default=1, help='Repeat real photos to extend the measured CPU workload')
args = parser.parse_args()
photos = sorted(p for p in args.folder.iterdir() if p.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp'})
if not photos or args.copies < 1 or len(photos) * args.copies > 60:
    parser.error('Use 1–60 images in total after copies; input must contain images.')
with zipfile.ZipFile(args.output, 'w', zipfile.ZIP_DEFLATED) as archive:
    for copy in range(args.copies):
        for index, photo in enumerate(photos):
            archive.write(photo, f'{copy:02d}_{index:03d}_{photo.name}')
print(f'Created {args.output} with {len(photos) * args.copies} actual image entries.')
