# Typing Baseline (mypy)

Tujuan: menambahkan pengecekan tipe statis tanpa memaksa refactor besar.
Kita mulai **longgar**, lalu perketat bertahap per modul.

## Instalasi
```bash
pip install mypy types-setuptools types-requests types-python-dateutil
# Jika Anda memakai Pydantic/SQLAlchemy, plugin otomatis terdeteksi dari mypy.ini
```

> Catatan: `ignore_missing_imports = True` untuk mencegah error paket tanpa stubs.
> Kita akan mematikan ini bertahap saat stubs tersedia.

## Menjalankan
```bash
mypy .
```

## Strategi Bertahap
1. **Baseline**: jalankan `mypy .` dan pastikan tidak gagal (karena konfigurasi longgar).
2. **Target per modul** (contoh `app/services`):
   - Tambahkan override di `mypy.ini`:
     ```ini
     [mypy-app.services.*]
     disallow_untyped_defs = True
     check_untyped_defs = True
     ```
   - Tambahkan type hints seperlunya sampai lulus.
3. **Naikkan standar**: pindahkan direktori lain ke aturan yang lebih ketat.

## Integrasi CI (GitHub Actions)
Tambahkan langkah berikut setelah lint:
```yaml
- name: Type check (mypy)
  run: |
    pip install mypy types-setuptools types-requests types-python-dateutil
    mypy .
```

## Pre-commit Hook
Tambahkan ke `.pre-commit-config.yaml`:
```yaml
- repo: https://github.com/pre-commit/mirrors-mypy
  rev: v1.11.2
  hooks:
    - id: mypy
      additional_dependencies:
        - pydantic
        - sqlalchemy
        - types-setuptools
        - types-requests
        - types-python-dateutil
      args: ["--config-file=mypy.ini"]
```
