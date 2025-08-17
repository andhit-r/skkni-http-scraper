# 🧾 Docstrings Standard

## Gaya
- Gunakan **Google style** untuk docstrings.
- Bahasa docstring: **English** (konsisten dengan kode).
- Tulis ringkas, jelaskan parameter, return, dan error.

## Contoh
```python
def parse_document(html: str) -> dict:
    """Parse SKKNI document page into a structured dict.

    Args:
        html: Raw HTML string of the document page.

    Returns:
        A dictionary with normalized fields (title, sector, units, ...).

    Raises:
        ValueError: If required sections are missing.
    """
    ...
```
