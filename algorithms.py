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
        return distance * cost_per_km
    elif stops == 1:
        return distance * cost_per_km * 0.85
    elif stops == 2:
        return distance * cost_per_km * 0.75
    else:
        return distance * cost_per_km * 0.7


def assign_neighbour(graph, departure_code, destination_code):
    neighbours = []
    routes = graph.get_routes(departure_code)

    if not routes:
        return neighbours

    destination_country = graph.airport_info[destination_code]["country"]

    for route in routes:
        neighbour = route["destination"]
        neighbour_info = graph.airport_info[neighbour]
        distance = route["km"]
        price = distance * 0.5

        # only add the neighbour if it is in the same country as destination
        if neighbour_info["country"] == destination_country:
            neighbours.append((neighbour, distance, price))

        return neighbours


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
                final_cost = base_cost * cabin_multiplier
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

    # Sort by cost or time
    if filter_type == "cheapest":
        # sort by final_cost => x[3]
        found_routes.sort(key=lambda x: x[3])
    else:
        # fastest => sort by total_time => x[2]
        found_routes.sort(key=lambda x: x[2])

    # If no routes were found, call assign_neighbour
    if not found_routes:
        print("No flights available.")
        # call the assign_neighbour function from your NeighbourAirport class.
        found_routes = assign_neighbour(graph, departure, destination)

    return found_routes
