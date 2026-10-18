"""Data sources: mock (for development) and real (Leclerc sheet + geolocator API)."""
import json
import math
import os
import re
from datetime import datetime

import gspread
import pandas as pd
import requests

from . import config as C

PLATES = ["AB-123-CD", "EF-456-GH", "IJ-789-KL", "MN-012-OP", "QR-345-ST", "UV-678-WX"]


def normalize_plate(p) -> str:
    """'ab-123 cd' -> 'AB123CD' so both apps can be matched."""
    return re.sub(r"[^A-Z0-9]", "", str(p).upper())


def gspread_client():
    raw = os.getenv("GOOGLE_CREDENTIALS")  # GitHub Actions: JSON content in a secret
    if raw:
        return gspread.service_account_from_dict(json.loads(raw))
    return gspread.service_account(filename=os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json"))


# ---------------------------- MOCK ----------------------------------------
def mock_leclerc(ts: datetime) -> pd.DataFrame:
    h = (ts - datetime(2026, 1, 1)).total_seconds() / 3600
    rows = []
    for i, plate in enumerate(PLATES):
        cycle = (h + i * 11) % 48                      # sawtooth: drains, then refuel
        fuel = round(95 - cycle / 48 * 80, 1)
        rows.append({
            "plate": plate,
            "fuel_level_pct": fuel,
            "last_refuel": (ts - pd.Timedelta(hours=cycle)).strftime("%Y-%m-%d %H:%M"),
            "engine_status": "OK" if i != 3 else "Check engine",
            "warnings": "" if fuel > 20 else "Low fuel",
        })
    return pd.DataFrame(rows)


def mock_geoloc(ts: datetime) -> pd.DataFrame:
    h = (ts - datetime(2026, 1, 1)).total_seconds() / 3600
    rows = []
    for i, plate in enumerate(PLATES):
        moving = (int(h) + i) % 3 != 0
        rows.append({
            "plate": plate.replace("-", ""),           # different format on purpose
            "lat": round(48.85 + math.sin(h / 5 + i) * 0.3, 5),
            "lon": round(2.35 + math.cos(h / 5 + i) * 0.4, 5),
            "speed_kmh": round(40 + 30 * abs(math.sin(h + i)), 1) if moving else 0,
            "odometer_km": int(100000 + i * 20000 + h * 35),
            "ignition": moving or i == 1,
            "gps_time": ts.strftime("%Y-%m-%d %H:%M"),
        })
    return pd.DataFrame(rows)


# ---------------------------- REAL ----------------------------------------
def real_leclerc() -> pd.DataFrame:
    ws = gspread_client().open_by_key(C.LECLERC_SHEET_ID).worksheet(C.LECLERC_WORKSHEET)
    df = pd.DataFrame(ws.get_all_records())
    return df.rename(columns=C.LECLERC_COLUMNS)[list(C.LECLERC_COLUMNS.values())]


def real_geoloc() -> pd.DataFrame:
    r = requests.get(C.GEO_API_URL, headers={C.GEO_AUTH_HEADER: C.GEO_AUTH_PREFIX + C.GEO_API_KEY}, timeout=30)
    r.raise_for_status()
    data = r.json()
    if C.GEO_RESPONSE_KEY:
        data = data[C.GEO_RESPONSE_KEY]
    df = pd.json_normalize(data).rename(columns=C.GEO_FIELDS)
    return df[[c for c in C.GEO_FIELDS.values() if c in df.columns]]


def get_data(ts: datetime):
    if C.USE_MOCK:
        return mock_leclerc(ts), mock_geoloc(ts)
    return real_leclerc(), real_geoloc()
