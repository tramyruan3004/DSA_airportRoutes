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
