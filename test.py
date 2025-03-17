import time
from collections import deque
from heapq import heappush, heappop
import json
import dataParser

CABIN_MULTIPLIERS = {
    "Economy": 1.0,
    "Premium Economy": 1.5,
    "Business": 2.0,
    "First": 2.5
}

def calculate_cost(distance, stops):
    cost_per_km = 0.3
    if stops == 0:
        return round(distance * cost_per_km, 2)
    elif stops == 1:
        return round(distance * cost_per_km * 0.85, 2)
    elif stops == 2:
        return round(distance * cost_per_km * 0.75, 2)
    else:
        return round(distance * cost_per_km * 0.7, 2)


def assign_neighbour(graph, departure_code, destination_code, cabin):
    neighbours = []
    routes = graph.get_routes(departure_code)

    if not routes:
        return neighbours

    destination_country = graph.airport_info[destination_code]["country"]

    for route in routes:
        neighbour = route["destination"]
        neighbour_info = graph.airport_info[neighbour]
        distance = route["km"]
        time = route["min"]
        price = round(distance * 0.5, 2)

        # only add the neighbour if it is in the same country as destination
        if neighbour_info["country"] == destination_country:
            neighbours.append(([departure_code, neighbour], distance, time, price, cabin))
    return neighbours

def find_one_way_flights_dijkstra(graph, departure, destination, stops=0, filter_type="cheapest", cabin="Economy"):
    found_routes = []
    
    # Priority queue: (priority, current_airport, route_list, distance_so_far, time_so_far)
    # Priority depends on filter_type (cost, time, or distance)
    priority_queue = []
    
    # Starting with departure airport
    initial_route = [departure]
    initial_dist = 0
    initial_time = 0
    
    # Calculate initial priority based on filter_type
    if filter_type == "cheapest":
        initial_priority = 0  # Initial cost is 0
    elif filter_type == "fastest":
        initial_priority = 0  # Initial time is 0
    else:  # shortest
        initial_priority = 0  # Initial distance is 0
    
    heappush(priority_queue, (initial_priority, departure, initial_route, initial_dist, initial_time))
    
    # To keep track of visited airports with their best path length
    # This helps avoid revisiting nodes with longer paths
    visited = {}  # {airport: min_stops_used}
    
    max_length = stops + 2  # e.g. stops=0 => route length=2
    
    while priority_queue:
        priority, current_airport, route_list, dist_so_far, time_so_far = heappop(priority_queue)
        
        # Current path length (including current airport)
        current_stops = len(route_list) - 1
        
        # Skip if we've already found a better path to this airport
        if current_airport in visited and visited[current_airport] <= current_stops:
            continue
        
        # Mark this airport as visited with current path length
        visited[current_airport] = current_stops
        
        # If we've reached the destination with valid number of stops
        if current_airport == destination and len(route_list) <= max_length:
            stops_so_far = len(route_list) - 2
            base_cost = calculate_cost(dist_so_far, stops_so_far)
            cabin_multiplier = CABIN_MULTIPLIERS.get(cabin, 1.0)
            final_cost = round(base_cost * cabin_multiplier, 2)
            found_routes.append((route_list, dist_so_far, time_so_far, final_cost, cabin))
            continue
        
        # If we've used all allowed stops plus the destination, don't explore further
        if len(route_list) >= max_length:
            continue
        
        # Explore neighboring airports
        for route in graph.get_routes(current_airport):
            neighbor = route["destination"]
            
            # Skip if already in route to avoid cycles
            if neighbor in route_list:
                continue
            
            new_dist = dist_so_far + route["km"]
            new_time = time_so_far + route["min"]
            new_route_list = route_list + [neighbor]
            
            # Calculate new priority based on filter_type
            if filter_type == "cheapest":
                stops_so_far = len(new_route_list) - 2
                base_cost = calculate_cost(new_dist, stops_so_far)
                cabin_multiplier = CABIN_MULTIPLIERS.get(cabin, 1.0)
                new_priority = round(base_cost * cabin_multiplier, 2)
            elif filter_type == "fastest":
                new_priority = new_time
            else:  # shortest
                new_priority = new_dist
            
            heappush(priority_queue, (new_priority, neighbor, new_route_list, new_dist, new_time))
    
    # Sort results based on filter_type (may not be necessary since Dijkstra already prioritizes)
    if filter_type == "cheapest":
        found_routes.sort(key=lambda x: x[3])
    elif filter_type == "fastest":
        found_routes.sort(key=lambda x: x[2])
    elif filter_type == "shortest":
        found_routes.sort(key=lambda x: x[1])
    
    # If no routes were found, call assign_neighbour
    if not found_routes:
        print("No direct flights available, looking into neighbouring airports.")
        # call the assign_neighbour function from your NeighbourAirport class.
        found_routes = assign_neighbour(graph, departure, destination, cabin)
    
    return found_routes

def find_one_way_flights(graph, departure, destination, stops=0, filter_type="cheapest", cabin="Economy"):
    found_routes = []
    # BFS queue: (current_airport, route_list, distance_so_far, time_so_far)
    queue = deque()
    queue.append((departure, [departure], 0, 0))

    max_length = stops + 2  # e.g. stops=0 => route length=2

    while queue:
        current_airport, route_list, dist_so_far, time_so_far = queue.popleft()

        if len(route_list) == max_length:
            if current_airport == destination:
                stops_so_far = len(route_list) - 2
                base_cost = calculate_cost(dist_so_far, stops_so_far)
                cabin_multiplier = CABIN_MULTIPLIERS.get(cabin, 1.0)
                final_cost = round(base_cost * cabin_multiplier, 2)
                found_routes.append((route_list, dist_so_far, time_so_far, final_cost, cabin))
            continue

        for route in graph.get_routes(current_airport):
            neighbor = route["destination"]
            if neighbor in route_list:
                continue
            new_dist = dist_so_far + route["km"]
            new_time = time_so_far + route["min"]
            new_route_list = route_list + [neighbor]
            queue.append((neighbor, new_route_list, new_dist, new_time))

    # Sort by cost, time or distance
    if filter_type == "cheapest":
        # cheapest => sort by final cost => x[3]
        found_routes.sort(key=lambda x: x[3])
    elif filter_type == "fastest":
        # fastest => sort by total time => x[2]
        found_routes.sort(key=lambda x: x[2])
    elif filter_type == "shortest":
        # shortest => sort by total distance => x[1]
        found_routes.sort(key=lambda x: x[1])
        
    # If no routes were found, call assign_neighbour
    if not found_routes:
        print("No direct flights available, looking into neighbouring airports.")
        # call the assign_neighbour function from your NeighbourAirport class.
        found_routes = assign_neighbour(graph, departure, destination, cabin)

    return found_routes


def find_multi_city_flights(graph, departure, middle, destination, stops, filter_type, cabin):
    found_routes = []
    firstHalfRoutes = find_one_way_flights(graph, departure, middle, stops, filter_type, cabin) # get routes from departure airport to middle airport
    for first in firstHalfRoutes:
        lastStop = first[0][-1] # to accomodate for neighbouring airports
        secondHalfRoutes = find_one_way_flights(graph, lastStop, destination, stops, filter_type, cabin) # check flights from last dest airport in first half to final dest airport
        for second in secondHalfRoutes:
            arr = []
            arr.append(list(first[0])+list(second[0][1:])) # airports
            arr.append(first[1] + second[1]) # total distance
            arr.append(first[2] + second[2]) # total time taken
            arr.append(first[3] + second[3]) # total costs
            print(first[3], second[3])
            found_routes.append(arr)
    print(found_routes)
    # Sort by cost, time or distance
    if filter_type == "cheapest":
        # cheapest => sort by final cost => x[3]
        found_routes.sort(key=lambda x: x[3])
    elif filter_type == "fastest":
        # fastest => sort by total time => x[2]
        found_routes.sort(key=lambda x: x[2])
    elif filter_type == "shortest":
        # shortest => sort by total distance => x[1]
        found_routes.sort(key=lambda x: x[1])
        
    print(found_routes)
    return found_routes

def measure_execution_time(graph, departure, destination, stops=2, filter_type="cheapest", cabin="Economy"):
    # Measure BFS implementation time
    start_time_bfs = time.time()
    bfs_result = find_one_way_flights(graph, departure, destination, stops, filter_type, cabin)
    end_time_bfs = time.time()
    bfs_execution_time = end_time_bfs - start_time_bfs
    
    # Measure Dijkstra implementation time
    start_time_dijkstra = time.time()
    dijkstra_result = find_one_way_flights_dijkstra(graph, departure, destination, stops, filter_type, cabin)
    end_time_dijkstra = time.time()
    dijkstra_execution_time = end_time_dijkstra - start_time_dijkstra
    
    # Print results
    print(f"BFS Execution Time: {bfs_execution_time:.6f} seconds")
    print(f"Dijkstra Execution Time: {dijkstra_execution_time:.6f} seconds")
    print(f"Difference: {dijkstra_execution_time - bfs_execution_time:.6f} seconds")
    
    # Compare routes found
    print(f"BFS found {len(bfs_result)} routes")
    print(f"Dijkstra found {len(dijkstra_result)} routes")
    
    # Compare the best route from each algorithm
    if bfs_result and dijkstra_result:
        bfs_best = bfs_result[0]
        dijkstra_best = dijkstra_result[0]
        
        print("\nBest route comparison:")
        print(f"BFS best route: {bfs_best[0]}, distance: {bfs_best[1]}, time: {bfs_best[2]}, cost: {bfs_best[3]}")
        print(f"Dijkstra best route: {dijkstra_best[0]}, distance: {dijkstra_best[1]}, time: {dijkstra_best[2]}, cost: {dijkstra_best[3]}")
    
    return {
        "bfs_time": bfs_execution_time,
        "dijkstra_time": dijkstra_execution_time,
        "bfs_routes": len(bfs_result),
        "dijkstra_routes": len(dijkstra_result),
        "bfs_result": bfs_result,
        "dijkstra_result": dijkstra_result
    }

# Load airport data
with open("dataset/airline_routes.json", "r") as file:
    airport_data = json.load(file)

# Initialize AirportGraph
airport_graph = dataParser.AirportGraph(airport_data)

# Parse airport coordinates
airport_coords = {
    iata: (float(info["latitude"]) if info.get("latitude") else None,
           float(info["longitude"]) if info.get("longitude") else None)
    for iata, info in airport_data.items()
}

# Filter out invalid coords
valid_airport_coords = {
    iata: (lat, lon)
    for iata, (lat, lon) in airport_coords.items()
    if lat is not None and lon is not None
}
# Example usage:
performance_data = measure_execution_time(airport_graph, "LAX", "ICN", stops=3, filter_type="cheapest", cabin="Economy")