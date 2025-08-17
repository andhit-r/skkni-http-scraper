# 0001 – Sumber Dependensi (Single Source of Truth)
Tanggal: 2025-08-17
Status: Disetujui

## Konteks
Proyek membutuhkan konsistensi pemasangan dependensi lintas lingkungan (lokal, CI, Docker). Perlu satu sumber kebenaran (single source of truth) agar versi paket tidak menyimpang.

## Keputusan
- Menggunakan **`pyproject.toml` + `requirements.txt`** (dikunci versi mayor/minor yang dibutuhkan).
- `pyproject.toml` mendefinisikan metadata proyek dan batas versi Python (`>=3.12,<3.13`).
- `requirements.txt` untuk reproducible install di Docker/CI.

## Konsekuensi
- Instalasi konsisten antara lokal dan CI/Docker.
- Perubahan dependensi harus mengubah keduanya (terdokumentasi di PR).
- Audit keamanan/pembaruan versi menjadi terpusat.
