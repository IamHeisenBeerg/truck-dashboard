import pandas as pd
import streamlit as st

st.set_page_config(page_title="Fleet Dashboard", layout="wide", page_icon="🚚")


@st.cache_data(ttl=300)
def load():
    try:  # real mode: Streamlit secrets hold the Google credentials
        import gspread
        gc = gspread.service_account_from_dict(dict(st.secrets["gcp_service_account"]))
        sh = gc.open_by_key(st.secrets["MASTER_SHEET_ID"])
        live = pd.DataFrame(sh.worksheet("Live").get_all_records())
        hist = pd.DataFrame(sh.worksheet("History").get_all_records())
    except Exception:  # mock mode: local CSV files
        live, hist = pd.read_csv("data/live.csv"), pd.read_csv("data/history.csv")
    hist["snapshot_time"] = pd.to_datetime(hist["snapshot_time"])
    return live, hist


live, hist = load()
st.title("🚚 Fleet Dashboard")
st.caption(f"Last update: {live['snapshot_time'].max()}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Trucks", len(live))
c2.metric("Moving", int((live["status"] == "Moving").sum()))
c3.metric("Low fuel", int((live["fuel_alert"] == "LOW").sum()))
c4.metric("Avg fuel", f"{pd.to_numeric(live['fuel_level_pct'], errors='coerce').mean():.0f}%")

left, right = st.columns(2)
with left:
    st.subheader("Map")
    st.map(live.rename(columns={"lat": "latitude", "lon": "longitude"})[["latitude", "longitude"]].dropna())
with right:
    st.subheader("Fuel level by truck")
    st.bar_chart(live.set_index("plate")["fuel_level_pct"])

st.subheader("Live table")
st.dataframe(
    live.style.apply(lambda r: ["background-color:#ffd6d6" if r["fuel_alert"] == "LOW" else "" for _ in r], axis=1),
    use_container_width=True,
)

st.subheader("History")
trucks = st.multiselect("Trucks", sorted(hist["plate"].unique()), default=sorted(hist["plate"].unique())[:3])
h = hist[hist["plate"].isin(trucks)].sort_values("snapshot_time")
st.line_chart(h.pivot_table(index="snapshot_time", columns="plate", values="fuel_level_pct"))

# Refuel events = fuel jumps of more than 15 points between two snapshots
h = hist.sort_values(["plate", "snapshot_time"]).copy()
h["fuel_level_pct"] = pd.to_numeric(h["fuel_level_pct"], errors="coerce")
h["jump"] = h.groupby("plate")["fuel_level_pct"].diff()
st.subheader("Detected refuels")
st.dataframe(h[h["jump"] > 15][["snapshot_time", "plate", "fuel_level_pct", "jump"]], use_container_width=True)
