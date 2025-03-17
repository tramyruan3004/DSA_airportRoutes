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

def find_one_way_flights(graph, departure, destination, stops=0, filter_type="cheapest", cabin="Economy"):
    found_routes = []
    # BFS queue: (current_airport, route_list, distance_so_far, time_so_far)
    queue = deque()
    queue.append((departure, [departure], 0, 0))

    max_length = stops + 2  # e.g. stops=0 => route length=2

    while queue:
        current_airport, route_list, dist_so_far, time_so_far = queue.popleft()

        # Modified condition: Check if we've reached destination with VALID stops (≤ max_length)
        # Instead of only adding routes with EXACTLY max_length
        if current_airport == destination and len(route_list) <= max_length and len(route_list) >= 2:
            stops_so_far = len(route_list) - 2
            base_cost = calculate_cost(dist_so_far, stops_so_far)
            cabin_multiplier = CABIN_MULTIPLIERS.get(cabin, 1.0)
            final_cost = round(base_cost * cabin_multiplier, 2)
            found_routes.append((route_list, dist_so_far, time_so_far, final_cost, cabin))
            # Don't continue exploring from destination (saves time)
            continue

        # Only explore further if we haven't exceeded max_length
        if len(route_list) < max_length:
            for route in graph.get_routes(current_airport):
                neighbor = route["destination"]
                if neighbor in route_list:
                    continue
                new_dist = dist_so_far + route["km"]
                new_time = time_so_far + route["min"]
                new_route_list = route_list + [neighbor]
                queue.append((neighbor, new_route_list, new_dist, new_time))

    # # Sort by cost, time or distance
    if filter_type == "cheapest":
        # cheapest => sort by final cost => x[3]
        found_routes.sort(key=lambda x: x[3])
    # elif filter_type == "fastest":
    #     # fastest => sort by total time => x[2]
    #     found_routes.sort(key=lambda x: x[2])
    # elif filter_type == "shortest":
    #     # shortest => sort by total distance => x[1]
    #     found_routes.sort(key=lambda x: x[1])
        
    # If no routes were found, call assign_neighbour
    if not found_routes:
        print("No direct flights available, looking into neighbouring airports.")
        # call the assign_neighbour function from your NeighbourAirport class.
        found_routes = assign_neighbour(graph, departure, destination, cabin)

    return found_routes


def find_one_way_flights_dijkstra_all(graph, departure, destination, stops=0, filter_type="cheapest", cabin="Economy"):
    found_routes = []
    
    # Priority queue: (priority, current_airport, route_list, distance_so_far, time_so_far)
    priority_queue = []
    
    # Starting with departure airport
    initial_route = [departure]
    initial_dist = 0
    initial_time = 0
    
    # Calculate initial priority based on filter_type
    initial_priority = 0  # All start at 0
    
    heappush(priority_queue, (initial_priority, departure, initial_route, initial_dist, initial_time))
    
    # Modified: Instead of using visited dict which prevents finding all routes,
    # use a set to track only cycles within a single path
    
    max_length = stops + 2  # e.g. stops=0 => route length=2
    
    while priority_queue:
        priority, current_airport, route_list, dist_so_far, time_so_far = heappop(priority_queue)
        
        # If we've reached the destination with valid number of stops (≤ max_length)
        if current_airport == destination and len(route_list) <= max_length and len(route_list) >= 2:
            stops_so_far = len(route_list) - 2
            base_cost = calculate_cost(dist_so_far, stops_so_far)
            cabin_multiplier = CABIN_MULTIPLIERS.get(cabin, 1.0)
            final_cost = round(base_cost * cabin_multiplier, 2)
            found_routes.append((route_list, dist_so_far, time_so_far, final_cost, cabin))
            # Don't continue exploring from destination (saves time)
            continue
        
        # Only explore further if we haven't exceeded max_length
        if len(route_list) < max_length:
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
    
    # Sort results based on filter_type
    if filter_type == "cheapest":
        found_routes.sort(key=lambda x: x[3])
    elif filter_type == "fastest":
        found_routes.sort(key=lambda x: x[2])
    elif filter_type == "shortest":
        found_routes.sort(key=lambda x: x[1])
    
    # If no routes were found, call assign_neighbour
    if not found_routes:
        print("No direct flights available, looking into neighbouring airports.")
        found_routes = assign_neighbour(graph, departure, destination, cabin)
    
    return found_routes

def find_one_way_flights_dijkstra_optimised(graph, departure, destination, stops=0, filter_type="cheapest", cabin="Economy"):
    found_routes = []
    priority_queue = []
    
    initial_route = [departure]
    initial_dist = 0
    initial_time = 0
    
    # Calculate initial priority based on filter_type
    if filter_type == "cheapest":
        initial_priority = 0
    elif filter_type == "fastest":
        initial_priority = 0
    else:  # shortest
        initial_priority = 0
    
    heappush(priority_queue, (initial_priority, departure, initial_route, initial_dist, initial_time))
    
    visited = {}  # {airport: min_stops_used}
    max_length = stops + 2  # e.g. stops=0 => route length=2
    
    while priority_queue:
        priority, current_airport, route_list, dist_so_far, time_so_far = heappop(priority_queue)
        
        # Modified: Match BFS behavior - only add routes of exact length
        if len(route_list) == max_length:
            if current_airport == destination:
                stops_so_far = len(route_list) - 2
                base_cost = calculate_cost(dist_so_far, stops_so_far)
                cabin_multiplier = CABIN_MULTIPLIERS.get(cabin, 1.0)
                final_cost = round(base_cost * cabin_multiplier, 2)
                found_routes.append((route_list, dist_so_far, time_so_far, final_cost, cabin))
            continue
        
        # Skip if we've already found a better path to this airport
        # This is what makes it Dijkstra's algorithm
        current_stops = len(route_list) - 1
        if current_airport in visited and visited[current_airport] <= current_stops:
            continue
        
        visited[current_airport] = current_stops
        
        # Stop exploring if we've reached max length
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
    
    # Sort results
    if filter_type == "cheapest":
        found_routes.sort(key=lambda x: x[3])
    elif filter_type == "fastest":
        found_routes.sort(key=lambda x: x[2])
    elif filter_type == "shortest":
        found_routes.sort(key=lambda x: x[1])
    
    # If no routes were found, call assign_neighbour
    if not found_routes:
        print("No direct flights available, looking into neighbouring airports.")
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

def compare_search_approaches(graph, departure, destination, max_stops=2):
    results = {
        "approach1_bfs": {"time": 0, "routes": []},
        "approach2_dijkstra": {"time": 0, "routes": []}
    }

    # Approach 1: Run BFS for all stops, then apply multiple filters
    start_time = time.time()
    
    all_bfs_routes = []
    for stops in range(max_stops + 1):
        routes = find_one_way_flights(graph, departure, destination, stops=stops, filter_type="cheapest")
        all_bfs_routes.extend(routes)
    
    # Create filtered versions for different criteria
    cheapest_routes = sorted(all_bfs_routes, key=lambda x: x[3])  # Sort by cost
    fastest_routes = sorted(all_bfs_routes, key=lambda x: x[2])   # Sort by time
    
    end_time = time.time()
    results["approach1_bfs"]["time"] = end_time - start_time
    results["approach1_bfs"]["routes"] = {
        "all": all_bfs_routes,
        "cheapest": cheapest_routes,
        "fastest": fastest_routes
    }
    print(results["approach1_bfs"]["routes"]["all"][:10])
    print("\n")
    print(results["approach1_bfs"]["routes"]["cheapest"][:10])
    print("\n")
    print(results["approach1_bfs"]["routes"]["fastest"][:10])
    print("\n========           =========\n")

    # Approach 2: Run Dijkstra for all stops, then apply multiple filters
    start_time = time.time()
    
    all_dijkstra_routes = []
    for stops in range(max_stops + 1):
        routes = find_one_way_flights_dijkstra_optimised(graph, departure, destination, stops=stops, filter_type="cheapest")
        all_dijkstra_routes.extend(routes)
    
    # Create filtered versions for different criteria
    cheapest_routes = sorted(all_dijkstra_routes, key=lambda x: x[3])  # Sort by cost
    fastest_routes = sorted(all_dijkstra_routes, key=lambda x: x[2])   # Sort by time
    
    end_time = time.time()
    results["approach2_dijkstra"]["time"] = end_time - start_time
    results["approach2_dijkstra"]["routes"] = {
        "all": all_dijkstra_routes,
        "cheapest": cheapest_routes,
        "fastest": fastest_routes
    }
    print(results["approach2_dijkstra"]["routes"]["all"][:10])
    print("\n")
    print(results["approach2_dijkstra"]["routes"]["cheapest"][:10])
    print("\n")
    print(results["approach2_dijkstra"]["routes"]["fastest"][:10])



    # Print comparison results
    print("=== Performance Comparison ===")
    print(f"Approach 1 (BFS → Sort): {results['approach1_bfs']['time']:.6f} seconds")
    print(f"Approach 2 (Dijkstra → Sort): {results['approach2_dijkstra']['time']:.6f} seconds")
    print(f"Difference: {results['approach2_dijkstra']['time'] - results['approach1_bfs']['time']:.6f} seconds")
    
    print("\n=== Routes Found ===")
    print(f"Approach 1 (BFS): {len(results['approach1_bfs']['routes']['all'])} total routes")
    print(f"Approach 2 (Dijkstra): {len(results['approach2_dijkstra']['routes']['all'])} total routes")
    
    print("\n=== Best Route Comparison ===")
    for filter_type in ["cheapest", "fastest"]:
        bfs_routes = results["approach1_bfs"]["routes"][filter_type]
        dijkstra_routes = results["approach2_dijkstra"]["routes"][filter_type]
        
        if bfs_routes and dijkstra_routes:
            bfs_best = bfs_routes[0]
            dijkstra_best = dijkstra_routes[0]
            
            print(f"\nFilter: {filter_type}")
            print(f"BFS best route: {bfs_best[0]}")
            print(f"  Distance: {bfs_best[1]}km, Time: {bfs_best[2]}min, Cost: ${bfs_best[3]}")
            
            print(f"Dijkstra best route: {dijkstra_best[0]}")
            print(f"  Distance: {dijkstra_best[1]}km, Time: {dijkstra_best[2]}min, Cost: ${dijkstra_best[3]}")
            
            # Compare key metrics
            if filter_type == "cheapest":
                metric_idx = 3  # Cost
                metric_name = "cost"
            else:  # fastest
                metric_idx = 2  # Time
                metric_name = "time"
                
            if bfs_best[metric_idx] != dijkstra_best[metric_idx]:
                print(f"⚠️ WARNING: Different {metric_name} values! BFS: {bfs_best[metric_idx]}, Dijkstra: {dijkstra_best[metric_idx]}")
    
    # Check if any routes are missing in Dijkstra that BFS found
    if len(results["approach1_bfs"]["routes"]["all"]) != len(results["approach2_dijkstra"]["routes"]["all"]):
        print("\n=== Missing Routes Analysis ===")
        
        # Create a set of route paths from BFS for easy comparison
        bfs_route_paths = set(tuple(route[0]) for route in results["approach1_bfs"]["routes"]["all"])
        dijkstra_route_paths = set(tuple(route[0]) for route in results["approach2_dijkstra"]["routes"]["all"])
        
        # Find routes in BFS but not in Dijkstra
        missing_in_dijkstra = bfs_route_paths - dijkstra_route_paths
        if missing_in_dijkstra:
            print(f"Routes found by BFS but missing in Dijkstra: {len(missing_in_dijkstra)}")
            # Print a sample of missing routes (up to 5)
            for i, route in enumerate(list(missing_in_dijkstra)[:5]):
                print(f"  {i+1}. {' → '.join(route)}")
        
        # Find routes in Dijkstra but not in BFS
        missing_in_bfs = dijkstra_route_paths - bfs_route_paths
        if missing_in_bfs:
            print(f"Routes found by Dijkstra but missing in BFS: {len(missing_in_bfs)}")
            # Print a sample of such routes (up to 5)
            for i, route in enumerate(list(missing_in_bfs)[:3000]):
                print(f"  {i+1}. {' → '.join(route)}")
    
    return results

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
comparison = compare_search_approaches(airport_graph, "HAN", "ICN", max_stops=2)