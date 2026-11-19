import numpy as np
import pandas as pd
import networkx as nx
import osmnx as ox
from sklearn.cluster import AgglomerativeClustering

# Settings
GRAPH_PATH = "map_data/klang_valley_drive.graphml"
CSV_PATH = "detailed_ev_charging_stations.csv"

DISTANCE_THRESHOLD = 2000
MAX_GROUP_SIZE = 2

pd.set_option("display.max_columns", None)

# Load road network
G = ox.load_graphml(GRAPH_PATH)
G = ox.convert.to_undirected(G)

# Load and clean station data
df = pd.read_csv(CSV_PATH)
df = df[["Station ID", "Latitude", "Longitude"]]
df = df.dropna(subset=["Station ID", "Latitude", "Longitude"])
df = df[df["Latitude"].between(-90, 90) & df["Longitude"].between(-180, 180)]
df = df.drop_duplicates(subset=["Station ID"]).reset_index(drop=True)

n = len(df)
print("Number of charging stations:", n)

nearest_nodes, snap_dist = ox.distance.nearest_nodes(
    G,
    X=df["Longitude"].values,
    Y=df["Latitude"].values,
    return_dist=True,
)
df["nearest_node"] = nearest_nodes
df["snap_dist"] = snap_dist

nodes = df["nearest_node"].to_numpy()
snaps = df["snap_dist"].to_numpy()

TOO_FAR = float(DISTANCE_THRESHOLD + 1)

node_distances = {}
for node in df["nearest_node"].unique():
    node_distances[node] = nx.single_source_dijkstra_path_length(
        G, source=node, weight="length", cutoff=DISTANCE_THRESHOLD
    )

D = np.full((n, n), TOO_FAR, dtype=float)
np.fill_diagonal(D, 0.0)

for i in range(n):
    reach = node_distances[nodes[i]]
    for j in range(i + 1, n):
        path = reach.get(nodes[j])
        if path is None:
            continue
        total = snaps[i] + path + snaps[j]
        if total <= DISTANCE_THRESHOLD:
            D[i, j] = D[j, i] = total

# Group stations based on road distance
# Complete linkage ensures every pair within a cluster meets the distance threshold.
if n > 1:
    labels = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=DISTANCE_THRESHOLD,
        metric="precomputed",
        linkage="complete",
    ).fit_predict(D)
else:
    labels = np.zeros(n, dtype=int)


# Split clusters to meet the team size limit
def split_cluster(indices, max_size):
    """Split clusters recursively until each group meets the maximum size."""
    if len(indices) <= max_size:
        return [indices]

    sub = D[np.ix_(indices, indices)]
    halves = AgglomerativeClustering(
        n_clusters=2, metric="precomputed", linkage="complete"
    ).fit_predict(sub)

    groups = []
    for h in (0, 1):
        part = [idx for idx, lab in zip(indices, halves) if lab == h]
        groups.extend(split_cluster(part, max_size))
    return groups


team_of = np.zeros(n, dtype=int)
next_team = 1
for cluster_id in np.unique(labels):
    members = list(np.where(labels == cluster_id)[0])
    for group in split_cluster(members, MAX_GROUP_SIZE):
        team_of[group] = next_team
        next_team += 1

df["Maintenance Team"] = team_of

# Generate team assignments
assignments_df = (
    df.groupby("Maintenance Team")
    .agg(
        Number_of_Stations=("Station ID", "count"),
        Station_IDs=("Station ID", list),
    )
    .reset_index()
)

print("\nMAINTENANCE TEAM ASSIGNMENTS")
print(assignments_df.to_string(index=False))

team_sizes = df.groupby("Maintenance Team")["Station ID"].transform("count")
total_teams = df["Maintenance Team"].nunique()
isolated = int((team_sizes == 1).sum())
shared = int((team_sizes > 1).sum())

print("\nMAINTENANCE ALLOCATION SUMMARY")
print("Total stations:", n)
print("Total maintenance teams:", total_teams)
print("Stations in shared teams:", shared)
print("Stations with their own team (isolated or unpaired):", isolated)
print("Largest team size:", int(team_sizes.max()), f"(cap = {MAX_GROUP_SIZE})")
print("Average stations per team:", round(n / total_teams, 2))
print("Reduction in teams vs one per station:", round((1 - total_teams / n) * 100, 2), "%")


df.to_csv("ev_station_team_assignments.csv", index=False)
# assignments_df.to_csv("ev_maintenance_team_summary.csv", index=False)
print("\nResults exported successfully.")