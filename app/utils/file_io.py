"""File IO helpers for saving CSV/XLSX if needed later."""

import pandas as pd


def save_csv(records: list[dict], path: str) -> None:
    pd.DataFrame(records).to_csv(path, index=False)


def save_xlsx(records: list[dict], path: str) -> None:
    pd.DataFrame(records).to_excel(path, index=False)
