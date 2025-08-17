# Linting Statis lintas format

Tujuan: lint otomatis untuk YAML, JSON, TOML, shell, serta guard umum (trailing whitespace, EOF, merge conflict).

## Tools via pre-commit
- pre-commit-hooks: check-yaml, check-json, check-toml, end-of-file-fixer, trailing-whitespace, mixed-line-ending, detect-private-key, debug-statements
- yamllint (via mirrors-yamllint)
- pretty-format-json (format JSON 2 spasi)
- shellcheck (lint shell script)
- Ruff (sudah ada untuk Python)

## Setup
```bash
pip install pre-commit
pre-commit install
pre-commit autoupdate  # opsional
```

## Jalankan manual
```bash
pre-commit run --all-files
```

> Catatan: Tidak menggunakan hadolint/markdownlint-cli sesuai preferensi proyek.
