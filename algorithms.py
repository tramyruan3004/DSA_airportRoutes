def find_direct_flights(graph, src, dest):
    #"""Find direct flights between two airports."""
    routes = graph.get_routes(src)
    direct_flights = [route for route in routes if route["destination"] == dest]
    return direct_flights

def find_cheapest_flight(graph, src, dest):
    #"""Find the cheapest flight between two airports."""
    routes = graph.get_routes(src)
    cheapest_flight = None
    for route in routes:
        if route["destination"] == dest:
            if cheapest_flight is None or route["km"] < cheapest_flight["km"]:
                cheapest_flight = route
    if cheapest_flight:
        return [(src, dest)]  # Return as a list of tuples (src, dest)
    else:
        return []

def find_shortest_path(graph, src, dest):
    #"""Find the shortest path between two airports using Dijkstra's algorithm."""
    import heapq

    distances = {airport: float('inf') for airport in graph.graph}
    distances[src] = 0
    previous_nodes = {airport: None for airport in graph.graph}
    pq = [(0, src)]

    while pq:
        current_distance, current_airport = heapq.heappop(pq)

        if current_airport == dest:
            break

        for route in graph.get_routes(current_airport):
            neighbor = route["destination"]
            distance = current_distance + route["km"]
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                previous_nodes[neighbor] = current_airport
                heapq.heappush(pq, (distance, neighbor))

    path = []
    current_airport = dest
    while previous_nodes[current_airport] is not None:
        path.insert(0, current_airport)
        current_airport = previous_nodes[current_airport]
    if path:
        path.insert(0, src)
    return path

def recommend_flights(graph, src, dest, route_type="direct"):
    # """Recommend flights based on the route type."""
    if route_type == "direct":
        direct_flights = find_direct_flights(graph, src, dest)
        if direct_flights:
            return [(src, dest)]  # Return as a list of tuples (src, dest)
        else:
            return []
    elif route_type == "cheapest":
        cheapest_flight = find_cheapest_flight(graph, src, dest)
        if cheapest_flight:
            return [(src, dest)]  # Return as a list of tuples (src, dest)
        else:
            return []
    elif route_type == "shortest":
        path = find_shortest_path(graph, src, dest)
        if path:
            return [path]  # Return the path as a list of airport codes
        else:
            return []
    return []

def find_multi_city_flights(graph, airports, route_type="direct"):
    #"""Find multi-city flights or recommend alternatives based on the route type."""
    if len(airports) < 2:
        return []

    all_flights = []
    for i in range(len(airports) - 1):
        src = airports[i]
        dest = airports[i + 1]
        flights = recommend_flights(graph, src, dest, route_type)
        if not flights:
            return []
        all_flights.append(flights)

    return all_flights