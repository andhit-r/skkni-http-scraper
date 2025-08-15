"""File IO helpers for saving CSV/XLSX if needed later."""
import pandas as pd
from typing import List, Dict

def save_csv(records: List[Dict], path: str) -> None:
    pd.DataFrame(records).to_csv(path, index=False)

def save_xlsx(records: List[Dict], path: str) -> None:
    pd.DataFrame(records).to_excel(path, index=False)
