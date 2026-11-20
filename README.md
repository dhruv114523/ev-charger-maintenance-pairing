# EV Charger Maintenance Pairing

This project pairs EV charging stations in Klang Valley into small maintenance teams based on road distance. It downloads the local road network, fetches charging station locations from Open Charge Map, and assigns nearby stations to teams with a maximum of two stations per team.

## How It Works

The scripts use the local road network rather than straight-line distance. Each station is snapped to the nearest road node, and stations connected by a 2 km or shorter driving route are grouped together using complete-link clustering. Oversized clusters are split into smaller teams so no team contains more than two stations; the final assignments include station IDs and team sizes.

## Data Flow

1. `download_map_data.py` downloads and saves the Klang Valley driving network.
2. `fetch_charging_station_data.py` uses Open Charge Map to create `detailed_ev_charging_stations.csv`.
3. `main.py` calculates driving distances, groups stations, and exports `ev_station_team_assignments.csv`.

## Setup

Install the dependencies:

```bash
pip install -r requirements.txt
```

Set an Open Charge Map API key in a `.env` file:

```text
OCM_API_KEY=your_api_key
```

## Usage

```bash
python download_map_data.py
python fetch_charging_station_data.py
python main.py
```

The grouping distance is 2 km and the team size limit is two stations. These values can be changed in `main.py`.

`exploration.ipynb` is currently only a placeholder for future exploration and is not part of the data flow.
