"""Writes results: local CSV (mock mode) or the Master Google Sheet (real mode)."""
from pathlib import Path

import pandas as pd

from . import config as C
from .sources import gspread_client

DATA = Path("data")


def _clean(df: pd.DataFrame) -> list:
    return df.astype(object).where(df.notna(), "").astype(str).values.tolist()


def _tab(sh, name):
    try:
        return sh.worksheet(name)
    except Exception:
        return sh.add_worksheet(title=name, rows=1000, cols=30)


def save(live: pd.DataFrame, history_rows: pd.DataFrame):
    if C.USE_MOCK:
        DATA.mkdir(exist_ok=True)
        live.to_csv(DATA / "live.csv", index=False)
        hist_path = DATA / "history.csv"
        header = not hist_path.exists()
        history_rows.to_csv(hist_path, mode="a", header=header, index=False)
        return
    sh = gspread_client().open_by_key(C.MASTER_SHEET_ID)
    ws = _tab(sh, "Live")
    ws.clear()
    ws.update(values=[live.columns.tolist()] + _clean(live), range_name="A1", value_input_option="USER_ENTERED")
    hs = _tab(sh, "History")
    if not hs.get_values("A1:A1"):
        hs.append_row(history_rows.columns.tolist())
    hs.append_rows(_clean(history_rows), value_input_option="USER_ENTERED")
