import os

import osmnx as ox
import pandas as pd
import requests
import dotenv

dotenv.load_dotenv()

GRAPH_PATH = "map_data/klang_valley_drive.graphml"
OUTPUT_CSV = "detailed_ev_charging_stations.csv"

API_KEY = os.environ.get("OCM_API_KEY")

API_URL = "https://api.openchargemap.io/v3/poi/"

G = ox.load_graphml(GRAPH_PATH)
nodes = ox.graph_to_gdfs(G, edges=False)
west, south, east, north = nodes.total_bounds
print(f"Search area: W={west:.4f} S={south:.4f} E={east:.4f} N={north:.4f}")

params = {
    "output": "json",
    "boundingbox": f"({south},{west}),({north},{east})",
    "maxresults": 10000,
    "compact": "true",
    "verbose": "false",
    "key": API_KEY,
}

print("Querying Open Charge Map...")
response = requests.get(API_URL, params=params, timeout=120)

if response.status_code != 200:
    raise SystemExit(
        f"Request failed: HTTP {response.status_code}\n"
        f"Server said: {response.text[:500]}"
    )

pois = response.json()
print("Raw stations returned:", len(pois))

if not pois:
    raise SystemExit("No charging stations found in this area.")

# Extract station details
rows = []
for poi in pois:
    addr = poi.get("AddressInfo") or {}
    rows.append(
        {
            "Station ID": f"ocm/{poi.get('ID')}",
            "Latitude": addr.get("Latitude"),
            "Longitude": addr.get("Longitude"),
            "Name": addr.get("Title"),
            "Address": addr.get("AddressLine1"),
            "Charge Points": poi.get("NumberOfPoints"),
        }
    )

stations = pd.DataFrame(rows)
stations = stations.dropna(subset=["Latitude", "Longitude"])
stations = stations.drop_duplicates(subset=["Station ID"])

# Filter stations to the map boundaries
stations = stations[
    stations["Longitude"].between(west, east)
    & stations["Latitude"].between(south, north)
].reset_index(drop=True)

# Export results
stations.to_csv(OUTPUT_CSV, index=False)

print(f"\nSaved {len(stations)} charging stations to {OUTPUT_CSV}")
print(stations.head(10).to_string(index=False))