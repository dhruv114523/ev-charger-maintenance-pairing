import pandas as pd

pd.set_option('display.max_columns', None)

df = pd.read_csv('detailed_ev_charging_stations.csv')

df = df[["Station ID", "Latitude", "Longitude"]] # other data is not relevant

# Remove rows with missing or invalid coordinates
df = df.dropna(subset=["Station ID", "Latitude", "Longitude"]).copy()

df = df[
    df["Latitude"].between(-90, 90) &
    df["Longitude"].between(-180, 180)
].copy()

# Remove duplicate station IDs
df = df.drop_duplicates(subset=["Station ID"])

# Reset index
df = df.reset_index(drop=True)

print("Number of chargers:", len(df))
print(df.head())