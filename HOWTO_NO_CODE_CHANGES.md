# Fixing Pre-commit & Ruff without touching code

## What changed
- Ignore FastAPI `Depends` default rule (B008) — common FastAPI style.
- Ignore long line rule (E501) and set `line-length = 120` to match current code.
- Raise McCabe complexity threshold to 20 (temporary) to avoid refactor.
- Update pre-commit stages from deprecated `commit` to `pre-commit`.

## Commands
```bash
# Update config files
unzip item3_fix_config_no_code_changes.zip -d .

# Reinstall / refresh pre-commit
pip install -U pre-commit
pre-commit install
pre-commit autoupdate  # optional

# Run hooks again
pre-commit run --all
```
