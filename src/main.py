"""Run: python -m src.main   (add --seed to create 3 days of fake history in mock mode)"""
import sys
from datetime import datetime, timedelta

import pandas as pd

from . import config as C
from .sheets import save
from .sources import get_data, normalize_plate


def build_live(leclerc: pd.DataFrame, geo: pd.DataFrame, ts: datetime) -> pd.DataFrame:
    leclerc, geo = leclerc.copy(), geo.copy()
    for df in (leclerc, geo):
        df["plate_key"] = df["plate"].map(normalize_plate)
    live = leclerc.merge(geo.drop(columns=["plate"]), on="plate_key", how="outer")

    speed = pd.to_numeric(live.get("speed_kmh"), errors="coerce")
    fuel = pd.to_numeric(live.get("fuel_level_pct"), errors="coerce")
    ign = live.get("ignition").astype(str).str.lower().isin(["true", "1", "on", "yes"])
    live["status"] = "Stopped"
    live.loc[ign, "status"] = "Idle"
    live.loc[speed > 3, "status"] = "Moving"
    live["fuel_alert"] = (fuel < C.FUEL_ALERT_PCT).map({True: "LOW", False: ""})
    live["snapshot_time"] = ts.strftime("%Y-%m-%d %H:%M")

    first = ["plate_key", "plate", "status", "fuel_level_pct", "fuel_alert", "snapshot_time"]
    return live[first + [c for c in live.columns if c not in first]]


def run_once(ts: datetime):
    leclerc, geo = get_data(ts)
    live = build_live(leclerc, geo, ts)
    save(live, live)  # each run: overwrite "Live", append snapshot to "History"
    return live


if __name__ == "__main__":
    if "--seed" in sys.argv and C.USE_MOCK:
        now = datetime.now().replace(minute=0, second=0, microsecond=0)
        for k in range(72, 0, -3):  # 3 days, every 3 hours
            run_once(now - timedelta(hours=k))
    live = run_once(datetime.now())
    print(f"OK: {len(live)} trucks synced at {datetime.now():%Y-%m-%d %H:%M}")
