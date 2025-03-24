from collections import deque, defaultdict
import heapq 

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
        if neighbour_info["country"] == destination_country:
            neighbours.append(([departure_code, neighbour], distance, time, price, cabin))
    return neighbours

def sort_routes_by_stops_and_price(routes):
    return sorted(routes, key=lambda r: (len(r[0]) - 2, r[3]))

def find_one_way_flights(graph, departure, destination, stops=0, cabin="Economy"):
    found_routes = []
    queue = deque()
    queue.append((departure, [departure], 0, 0))
    max_length = stops + 2
    while queue:
        current_airport, route_list, dist_so_far, time_so_far = queue.popleft()
        if current_airport == destination and len(route_list) <= max_length and len(route_list) >= 2:
            stops_so_far = len(route_list) - 2
            base_cost = calculate_cost(dist_so_far, stops_so_far)
            cabin_multiplier = CABIN_MULTIPLIERS.get(cabin, 1.0)
            final_cost = round(base_cost * cabin_multiplier, 2)
            found_routes.append((route_list, dist_so_far, time_so_far, final_cost, cabin))
            continue
        if len(route_list) < max_length:
            for route in graph.get_routes(current_airport):
                neighbor = route["destination"]
                if neighbor in route_list:
                    continue
                new_dist = dist_so_far + route["km"]
                new_time = time_so_far + route["min"]
                new_route_list = route_list + [neighbor]
                queue.append((neighbor, new_route_list, new_dist, new_time))
    if not found_routes:
        print("No direct flights available, looking into neighbouring airports.")
        found_routes = assign_neighbour(graph, departure, destination, cabin)
    found_routes = sort_routes_by_stops_and_price(found_routes)
    return found_routes

def find_multi_city_flights(graph, departure, middle, destination, stops, filter_type, cabin):
    found_routes = []
    firstHalfRoutes = find_one_way_flights(graph, departure, middle, stops, cabin)
    for first in firstHalfRoutes:
        lastStop = first[0][-1]
        secondHalfRoutes = find_one_way_flights(graph, lastStop, destination, stops, cabin)
        for second in secondHalfRoutes:
            arr = []
            arr.append(list(first[0]) + list(second[0][1:]))
            arr.append(first[1] + second[1])
            arr.append(first[2] + second[2])
            arr.append(first[3] + second[3])
            arr.append(cabin)
            found_routes.append(arr)
    if filter_type == "cheapest":
        found_routes = sort_routes_by_stops_and_price(found_routes)
    elif filter_type == "fastest":
        found_routes.sort(key=lambda x: x[2])
    elif filter_type == "shortest":
        found_routes.sort(key=lambda x: x[1])
    return found_routes


def find_one_way_flights_dijkstra(graph, departure, destination, stops=0, cabin="Economy"):
    found_routes = []
    max_stops = stops
    
    # Priority queue: (total_distance, stops_used, current_airport, path, distance, time)
    heap = []
    heapq.heappush(heap, (0, 0, departure, [departure], 0, 0))
    
    # Track best distances for (airport, stops_used) pairs
    best_distances = defaultdict(lambda: float('inf'))
    best_distances[(departure, 0)] = 0
    
    while heap:
        dist, stops_used, airport, path, path_dist, path_time = heapq.heappop(heap)
        
        # Skip if we already have a better path to this airport with same or fewer stops
        if dist > best_distances[(airport, stops_used)]:
            continue
        
        # Found a valid route to destination
        if airport == destination and len(path) >= 2:
            # Calculate cost
            base_cost = calculate_cost(path_dist, stops_used)
            final_cost = round(base_cost * CABIN_MULTIPLIERS.get(cabin, 1.0), 2)
            
            # Add to results
            found_routes.append((path, path_dist, path_time, final_cost, cabin))
            
            # Mark if this is a direct flight
            if stops_used == 0:
                direct_flights_found = True
            continue
        
        # Stop if we've used all allowed stops
        if stops_used >= max_stops:
            continue
        
        # Explore all connections
        for route in graph.get_routes(airport):
            neighbor = route["destination"]
            if neighbor in path:  # Prevent cycles
                continue
            
            new_dist = path_dist + route["km"]
            new_time = path_time + route["min"]
            new_stops = stops_used + (0 if neighbor == destination else 1)
            new_path = path + [neighbor]
            
            # Only proceed if this path is better than previous ones
            if new_dist < best_distances[(neighbor, new_stops)]:
                best_distances[(neighbor, new_stops)] = new_dist
                heapq.heappush(heap, (new_dist, new_stops, neighbor, new_path, new_dist, new_time))
    
    # If no routes found, try neighboring airports
    if not found_routes:
        print("No direct flights available, looking into neighbouring airports.")
        found_routes = assign_neighbour(graph, departure, destination, cabin)
    
    # Sort by: 1. Number of stops, 2. Distance, 3. Time
    # found_routes.sort(key=lambda x: (len(x[0])-2, x[1], x[2]))
    
    return found_routes

def find_optimal_flights_complete(graph, departure, destination, max_stops=2, cabin="Economy"):
    
    # Initialize data structures
    heap = []
    heapq.heappush(heap, (0, 0, departure, [departure], 0))  # (dist, stops, node, path, time)
    
    # Track best distances for (node, stops) pairs
    best_dist = defaultdict(lambda: float('inf'))
    best_dist[(departure, 0)] = 0
    
    found_routes = []
    found_direct = False

    while heap:
        current_dist, stops, node, path, time = heapq.heappop(heap)
        
        # Skip if we found a better path to this node with same or fewer stops
        if current_dist > best_dist[(node, stops)]:
            continue
            
        # Found a valid route to destination
        if node == destination and len(path) >= 2:
            cost = calculate_cost(current_dist, stops)
            final_cost = round(cost * CABIN_MULTIPLIERS.get(cabin, 1.0), 2)
            found_routes.append((path, current_dist, time, final_cost, cabin))
            
            if stops == 0:  # Mark direct flight found
                found_direct = True
            continue
        
        # Stop expanding if we've reached max stops
        if stops >= max_stops:
            continue
            
        # Explore neighbors
        for route in graph.get_routes(node):
            neighbor = route["destination"]
            if neighbor in path:  # Prevent cycles
                continue
                
            new_dist = current_dist + route["km"]
            new_time = time + route["min"]
            new_stops = stops + (1 if neighbor != destination else 0)
            new_path = path + [neighbor]
            
            # Only proceed if this path is better
            if new_dist < best_dist[(neighbor, new_stops)]:
                best_dist[(neighbor, new_stops)] = new_dist
                heapq.heappush(heap, (new_dist, new_stops, neighbor, new_path, new_time))
    
    # Early return if we only wanted direct flights and found some
    if max_stops == 0 and found_direct:
        return [route for route in found_routes if len(route[0]) == 2]
    
    # Sort by stops then distance
    found_routes.sort(key=lambda x: (len(x[0])-2, x[1]))
    
    return found_routes