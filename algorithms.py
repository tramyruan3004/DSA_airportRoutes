import json
import dataParser
from collections import deque

class NeighbourAirport:
    def __init__(self, graph):
        self.graph = graph

    def assign_neighbour(self, departure_code, destination_code):
        neighbours = []
        routes = self.graph.get_routes(departure_code)

        if not routes:
            print(f"No neighbouring airports from {departure_code}.")
            return neighbours

        print(
            f"\nRecommended Flights from {departure_code} to neighbouring airports in {self.graph.airport_info[destination_code]['country']}:"
        )

        destination_country = self.graph.airport_info[destination_code]["country"]

        for route in routes:
            neighbour = route["destination"]
            neighbour_info = self.graph.airport_info[neighbour]
            distance = route["km"]
            price = distance * 0.5

            if neighbour_info["country"] == destination_country:
                print(
                    f"{departure_code} → {neighbour} ({neighbour_info['name']})"
                )
                print(f"Distance from {destination_code}: {distance} km")
                print(f"Price: ${price:.2f}\n")
                neighbours.append(neighbour)

        if not neighbours:
            print("No recommended neighbouring airports found in the destination country.")

        return neighbours


class SearchAlgorithm:
    def __init__(self, graph):
        self.graph = graph
        self.neighbour_algo = NeighbourAirport(graph)

    def bfs(self, departure, destination, max_stops, direct_flight_price):
        queue = deque([(departure, [departure], 0, 0, 0, 0)])
        found_routes = []

        if self.graph.get_distance(departure, destination) > 8000:
            max_stops = 2
            max_depth = 5

        while queue:
            current, path, distance, timing, price, stops = queue.popleft()

            if len(found_routes) >= 8:
                return sorted(found_routes, key=lambda x: x[3])

            if current == destination:
                if price < direct_flight_price:
                    found_routes.append((path, distance, timing, price))
                continue

            if stops > max_stops:
                continue

            routes = self.graph.get_routes(current)
            routes = sorted(routes, key=lambda x: self.graph.get_distance(x["destination"], destination))

            for route in routes:
                neighbour = route["destination"]

                if neighbour not in path:
                    new_distance = distance + route["km"]
                    new_timing = timing + route["min"]

                    if stops == 0:
                        new_price = new_distance * 0.5
                    elif stops == 1:
                        new_price = new_distance * 0.5 * 0.9
                    elif stops == 2:
                        new_price = new_distance * 0.5 * 0.8
                    else:
                        new_price = new_distance * 0.5 * 0.7

                    if new_distance > direct_flight_price * 1.5:
                        continue

                    queue.append((neighbour, path + [neighbour], new_distance, new_timing, new_price, stops + 1))

        found_routes = sorted(found_routes, key=lambda x: x[3])
        for path, distance, timing, price in found_routes:
            print(f"Alternative Route: {' → '.join(path)}")
            print(f"  Total Distance: {distance} km")
            print(f"  Total Timing: {timing} min")
            print(f"  Price: ${price:.2f}\n")

        return found_routes

    def search_routes(self, departure, destination, max_stops=3):
        if departure not in self.graph.airport_info or destination not in self.graph.airport_info:
            print(f"{departure} or {destination} not found.")
            return

        print(f"\nPossible routes from {departure} to {destination}:")

        direct_route = None
        direct_flight_price = float('inf')

        for route in self.graph.get_routes(departure):
            if route["destination"] == destination:
                direct_route = route
                direct_flight_price = route["km"] * 0.5
                break

        found_any_flight = False

        if direct_route:
            print(f"\n!Direct Flight Available!")
            print(f"{departure} → {destination}")
            print(f"  Distance: {direct_route['km']} km")
            print(f"  Timing: {direct_route['min']} min")
            print(f"  Price: ${direct_flight_price:.2f}\n")
            found_any_flight = True
        else:
            print("!No Direct Flight Available!")

        print("Searching for alternative layover routes...")
        routes = self.bfs(departure, destination, max_stops, direct_flight_price)

        if routes:
            found_any_flight = True
            for path, distance, timing, price in routes:
                print(f"Alternative Route: {' → '.join(path)}")
                print(f"  Total Distance: {distance} km")
                print(f"  Total Timing: {timing} min")
                print(f"  Price: ${price:.2f}\n")
        elif found_any_flight:
            print("!No alternative layover routes needed. The direct flight is already optimal!\n")

        if not found_any_flight:
            print("!No flights available!")
            self.neighbour_algo.assign_neighbour(departure, destination)


if __name__ == "__main__":
    with open("dataset/airline_routes.json", "r") as f:
        data = json.load(f)

    airport_graph = dataParser.AirportGraph(data)
    airport_graph.display_graph()

    print("List of Airport Codes:")
    for code, info in airport_graph.airport_info.items():
        print(f"{code} ({info['name']})")

    search_algo = SearchAlgorithm(airport_graph)

    departure = input("Enter Departure Airport Code: ").strip().upper()
    destination = input("Enter Destination Airport Code: ").strip().upper()

    search_algo.search_routes(departure, destination)
