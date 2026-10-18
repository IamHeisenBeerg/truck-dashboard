import os

USE_MOCK = os.getenv("USE_MOCK", "true").lower() == "true"
LECLERC_SHEET_ID = os.getenv("LECLERC_SHEET_ID", "")
LECLERC_WORKSHEET = os.getenv("LECLERC_WORKSHEET", "Sheet1")
MASTER_SHEET_ID = os.getenv("MASTER_SHEET_ID", "")
GEO_API_URL = os.getenv("GEO_API_URL", "")
GEO_API_KEY = os.getenv("GEO_API_KEY", "")
FUEL_ALERT_PCT = float(os.getenv("FUEL_ALERT_PCT", "20"))

# ---- EDIT THESE when you see the real data -------------------------------
# Real column name in the Leclerc sheet -> standard name used by this project
LECLERC_COLUMNS = {
    "Immatriculation": "plate",
    "Niveau carburant": "fuel_level_pct",
    "Dernier plein": "last_refuel",
    "Etat": "engine_status",
    "Alertes": "warnings",
}

# Field name in the geolocator API JSON -> standard name
# (nested fields use dots, e.g. "position.lat": "lat")
GEO_FIELDS = {
    "registration": "plate",
    "latitude": "lat",
    "longitude": "lon",
    "speed": "speed_kmh",
    "mileage": "odometer_km",
    "ignition": "ignition",
    "timestamp": "gps_time",
}
# If the API wraps the list, e.g. {"vehicles": [...]}, put "vehicles" here
GEO_RESPONSE_KEY = ""
# How the API key is sent. Adapt to the API docs.
GEO_AUTH_HEADER = "Authorization"
GEO_AUTH_PREFIX = "Bearer "
# ---------------------------------------------------------------------------
