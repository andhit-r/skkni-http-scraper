# Gaya Kode: Formatting & Imports

## Tooling
- **Formatter**: Ruff Formatter
- **Import sorting**: isort via Ruff (rule `I`)
- **Lint dasar**: pyflakes/pycodestyle/pep8-naming/pyupgrade/bugbear

## Perintah Lokal
Format semua file:
```bash
ruff format .
```

Lint + perbaikan otomatis:
```bash
ruff check . --fix
```

## Pre-commit
Aktifkan pre-commit:
```bash
pip install pre-commit
pre-commit install
```
Setelah itu, setiap `git commit` akan menjalankan `ruff-format` dan `ruff check --fix`.

## Catatan
- Panjang baris: **100**.
- Kutip: **double quote** default.
- Target Python: **3.12**.
- Folder yang diabaikan: `.venv/`, `data/`, file DB contoh.
