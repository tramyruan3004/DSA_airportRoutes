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
            neighbours.append(([departure_code, neighbour], distance, time, price, cabin, "Alternative via Nearby Airport"))
    return neighbours

def sort_routes_by_stops_and_price(routes):
    return sorted(routes, key=lambda r: (len(r[0]) - 2, r[3]))

def quicksort_routes_by_stops_and_price(routes):
    if len(routes) <= 1:
        return routes
    
    pivot = routes[len(routes) // 2]
    pivot_stops = len(pivot[0]) - 2
    pivot_price = pivot[3]
    
    less = [route for route in routes if (len(route[0]) - 2, route[3]) < (pivot_stops, pivot_price)]
    equal = [route for route in routes if (len(route[0]) - 2, route[3]) == (pivot_stops, pivot_price)]
    greater = [route for route in routes if (len(route[0]) - 2, route[3]) > (pivot_stops, pivot_price)]
    
    return quicksort_routes_by_stops_and_price(less) + equal + quicksort_routes_by_stops_and_price(greater)

def quicksort_routes_by_stops_and_distance(routes):
    if len(routes) <= 1:
        return routes
    
    pivot = routes[len(routes) // 2]
    pivot_stops = len(pivot[0]) - 2
    pivot_dist = pivot[1]
    
    less = [route for route in routes if (len(route[0]) - 2, route[1]) < (pivot_stops, pivot_dist)]
    equal = [route for route in routes if (len(route[0]) - 2, route[1]) == (pivot_stops, pivot_dist)]
    greater = [route for route in routes if (len(route[0]) - 2, route[1]) > (pivot_stops, pivot_dist)]
    
    return quicksort_routes_by_stops_and_distance(less) + equal + quicksort_routes_by_stops_and_distance(greater)

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
            found_routes.append((route_list, dist_so_far, time_so_far, final_cost, cabin, "Standard Route"))
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
    found_routes = quicksort_routes_by_stops_and_price(found_routes)
    # found_routes = sort_routes_by_stops_and_price(found_routes)
    return found_routes

def find_one_way_flights_dijkstra(graph, departure, destination, stops=0, cabin="Economy"):
    found_routes = []
    max_stops = stops

    heap = []
    heapq.heappush(heap, (0, 0, departure, [departure], 0, 0))

    best_distances = defaultdict(lambda: float('inf'))
    best_distances[(departure, 0)] = 0

    while heap:
        dist, stops_used, airport, path, path_dist, path_time = heapq.heappop(heap)

        if dist > best_distances[(airport, stops_used)]:
            continue

        if airport == destination and len(path) >= 2:
            base_cost = calculate_cost(path_dist, stops_used)
            final_cost = round(base_cost * CABIN_MULTIPLIERS.get(cabin, 1.0), 2)
            found_routes.append((path, path_dist, path_time, final_cost, cabin, "Standard Route"))
            continue

        if stops_used >= max_stops:
            continue

        for route in graph.get_routes(airport):
            neighbor = route["destination"]
            if neighbor in path:
                continue
            new_dist = path_dist + route["km"]
            new_time = path_time + route["min"]
            new_stops = stops_used + (0 if neighbor == destination else 1)
            new_path = path + [neighbor]
            if new_dist < best_distances[(neighbor, new_stops)]:
                best_distances[(neighbor, new_stops)] = new_dist
                heapq.heappush(heap, (new_dist, new_stops, neighbor, new_path, new_dist, new_time))

    if not found_routes:
        print("No direct flights available, looking into neighbouring airports.")
        found_routes = assign_neighbour(graph, departure, destination, cabin)

    return found_routes

def find_optimal_flights_complete(graph, departure, destination, max_stops=2, cabin="Economy"):
    heap = []
    heapq.heappush(heap, (0, 0, departure, [departure], 0))
    best_dist = defaultdict(lambda: float('inf'))
    best_dist[(departure, 0)] = 0
    found_routes = []
    found_direct = False

    while heap:
        current_dist, stops, node, path, time = heapq.heappop(heap)
        if current_dist > best_dist[(node, stops)]:
            continue
        if node == destination and len(path) >= 2:
            cost = calculate_cost(current_dist, stops)
            final_cost = round(cost * CABIN_MULTIPLIERS.get(cabin, 1.0), 2)
            found_routes.append((path, current_dist, time, final_cost, cabin, "Standard Route"))
            if stops == 0:
                found_direct = True
            continue
        if stops >= max_stops:
            continue
        for route in graph.get_routes(node):
            neighbor = route["destination"]
            if neighbor in path:
                continue
            new_dist = current_dist + route["km"]
            new_time = time + route["min"]
            new_stops = stops + (1 if neighbor != destination else 0)
            new_path = path + [neighbor]
            if new_dist < best_dist[(neighbor, new_stops)]:
                best_dist[(neighbor, new_stops)] = new_dist
                heapq.heappush(heap, (new_dist, new_stops, neighbor, new_path, new_time))

    if max_stops == 0 and found_direct:
        return [route for route in found_routes if len(route[0]) == 2]

    found_routes = quicksort_routes_by_stops_and_distance(found_routes)
    # found_routes.sort(key=lambda x: (len(x[0])-2, x[1]))
    return found_routes

def find_multi_city_flights(graph, departure, middle, destination, max_stops = 1, filter_type='cheapest', cabin='Economy'):
    all_routes = []
    first_half_routes = find_one_way_flights(graph, departure, middle, stops=max_stops)
    for r1 in first_half_routes:
        mid = r1[0][-1]
        second_half_routes = find_one_way_flights(graph, mid, destination, stops=max_stops)
        for r2 in second_half_routes:
            full_path = r1[0] + r2[0][1:]
            total_dist = r1[1] + r2[1]
            total_time = r1[2] + r2[2]
            total_cost = round(r1[3] + r2[3], 2)
            label = "Alternative via Nearby Airport" if (len(r1) >= 6 and r1[5] == "Alternative via Nearby Airport") or (len(r2) >= 6 and r2[5] == "Alternative via Nearby Airport") else "Standard Route"
            all_routes.append((full_path, total_dist, total_time, total_cost, cabin, label))
    all_routes = quicksort_routes_by_stops_and_price(all_routes)    
    # all_routes = sort_routes_by_stops_and_price(all_routes)
    return all_routes
