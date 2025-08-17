# 🧩 Commit Standards (Conventional Commits)

## Format
```
<type>(<optional-scope>): <subject>
```
**type** yang digunakan: `feat`, `fix`, `docs`, `refactor`, `chore`, `test`, `build`, `ci`.

## Contoh
- `feat(api): tambah endpoint search-documents`
- `fix(scraper): perbaiki parsing sektor`
- `docs: update README dengan kebijakan bahasa`

## Aturan Singkat
- Subject maksimal ±72 karakter, kalimat ringkas.
- Satu PR = satu tujuan perubahan yang jelas.
- Gunakan body commit bila butuh konteks tambahan atau breaking change.
