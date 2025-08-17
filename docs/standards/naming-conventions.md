# 🏷️ Naming Conventions

## Python (kode & paket)
- **Package/module**: `snake_case` (contoh: `skkni_service.py`, `playwright_helper.py`)
- **Class**: `PascalCase` (contoh: `SkkniService`)
- **Function/variable**: `snake_case` (contoh: `parse_document`, `cache_ttl_days`)
- **Constant**: `UPPER_SNAKE_CASE` (contoh: `DEFAULT_LIMIT`)
- **Private**: awali dengan `_` (contoh: `_parse_html()`)

## API (path & parameter)
- **Path**: kebab-case singkat, plural bila koleksi (contoh: `/skkni/search-documents`)
- **Query param**: `snake_case` (contoh: `page_from`, `force_refresh`)

## Database/Model
- **Tabel**: `snake_case_plural` (contoh: `skkni_units`)
- **Kolom**: `snake_case`
- **Primary key**: `id` (integer/uuid)
- **Foreign key**: `<table>_id`

## File & Direktori
- **Python file**: `snake_case.py`
- **Config**: ekstensi sesuai (yml, toml, ini)
- **Tests**: `tests/test_<area>.py`, gunakan nama test yang deskriptif

## Komit & Branch
- **Branch**: `feat/<ringkas>`, `fix/<ringkas>`, `chore/<ringkas>`
- **Commit**: ikuti Conventional Commits (lihat `docs/standards/commits.md`)
