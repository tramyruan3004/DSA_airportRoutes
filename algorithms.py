from collections import deque

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
