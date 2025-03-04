import json
import dataParser

with open("dataset/airline_routes.json", "r") as f:
    data = json.load(f)

# Create graph
airport_graph = dataParser.AirportGraph(data)

# Display graph
airport_graph.display_graph()