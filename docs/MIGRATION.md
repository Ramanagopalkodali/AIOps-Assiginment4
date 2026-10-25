# Switch from the previous layout

Extract the new ZIP into your home directory, creating ~/DA3408-A4-clean. Keep
~/DA3408-A4-MacVM until your model files, evidence, photos and disclosure are copied.

```bash
unzip ~/Downloads/DA3408-A4-restructured.zip -d ~/
conda activate aiops
cd ~/DA3408-A4-clean
python scripts/migrate_local_data.py ~/DA3408-A4-MacVM
chmod +x scripts/*.sh
```

Do not extract over a directory of the same name with local changes. The migration
script copies missing files only, retains the old folder, and saves any previous
AI disclosure as docs/previous_AI_DISCLOSURE.md for you to review and merge.
An interrupted download may have no complete models/blip-base weights; reuse of
the shared Hugging Face cache happens naturally when setup_model.py is rerun.
The old Conda environment is independent of both project directories.

| Previous command/path | New command/path |
|---|---|
| python build_dashboard.py | python scripts/build_dashboard.py |
| python -m unittest discover -s tests -v | bash scripts/run_tests.sh |
| python alert_receiver.py | bash scripts/run_receiver.sh |
| bash scripts/run_backend.sh | Same command; launches package with python -m |
| bash scripts/run_app.sh | Same command; launches src/caption_app/ui.py |
| prometheus.yml | monitoring/prometheus.yml |
| metrics.py, backend.py, image_inputs.py | src/caption_app/ |
| app.py | src/caption_app/ui.py |
| METRICS_AND_VIVA.md | docs/METRICS_AND_VIVA.md |

Imports are now package-relative; model paths resolve from the repository root,
not the current shell directory. Tests share an explicit tests package. Launch
scripts use aiops if active, otherwise the project's .venv if it exists. No
dependency installation occurs in those launch scripts.

If the old project already has a Git history, keep that folder and history. This
download is a source export, not a clone containing your .git metadata; do not
delete the old repository. Migrating Git history is separate from copying data.
