"""Copy local data from the previous layout; never delete or overwrite files."""
import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('old_project', type=Path)
args = parser.parse_args()
old = args.old_project.expanduser().resolve()
if old == ROOT:
    parser.error('Choose the old project, not this directory.')
if not (old / 'app.py').is_file() and not (old / 'src/caption_app/ui.py').is_file():
    parser.error('The source does not look like the previous captioning project.')


def copy_missing(source, destination):
    if not source.is_file():
        return
    if destination.exists():
        print('Kept existing:', destination.relative_to(ROOT))
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    print('Copied:', destination.relative_to(ROOT))


for folder in ('models', 'demo_inputs'):
    for source in (old / folder).rglob('*'):
        copy_missing(source, ROOT / folder / source.relative_to(old / folder))
for source in (old / 'sample_photos').rglob('*'):
    copy_missing(source, ROOT / 'demo_inputs/bulk/photos' / source.relative_to(old / 'sample_photos'))
for name in ('demo.zip', 'demo-long.zip'):
    copy_missing(old / name, ROOT / 'demo_inputs/bulk/archives' / name)
for source in (old / 'evidence').rglob('*'):
    if not source.is_file() or source.name == 'README.md':
        continue
    rel = source.relative_to(old / 'evidence')
    if rel.parts[0] in ('screenshots', 'logs', 'results', 'video'):
        destination = ROOT / 'evidence' / rel
    else:
        ext = source.suffix.lower()
        category = ('screenshots' if ext in {'.png', '.jpg', '.jpeg', '.webp'} else
                    'video' if ext in {'.mp4', '.mov', '.mkv'} else
                    'results' if ext == '.csv' else 'logs')
        destination = ROOT / 'evidence' / category / 'previous-layout' / rel
    copy_missing(source, destination)
copy_missing(old / 'requirements-installed.txt', ROOT / 'requirements-installed.txt')
copy_missing(old / 'AI_DISCLOSURE.md', ROOT / 'docs/previous_AI_DISCLOSURE.md')
print('Finished. Old project retained. Review docs/previous_AI_DISCLOSURE.md and merge your own disclosure.')
