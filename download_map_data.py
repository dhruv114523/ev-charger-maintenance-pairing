import osmnx as ox

bbox = (101.35, 2.80, 101.90, 3.40)
G = ox.graph_from_bbox(bbox, network_type="drive")
ox.save_graphml(G, "map_data/klang_valley_drive.graphml")