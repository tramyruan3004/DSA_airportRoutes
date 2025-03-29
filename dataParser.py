class AirportGraph:
    def __init__(self, data):
        self.graph = {}
        self.airport_info = {}
        self.build_graph(data)
    
    def build_graph(self, data):
        for iata, airport in data.items():
            self.airport_info[iata] = {
                "name": airport["name"],
                "country": airport["country"],
                "country_code": airport["country_code"],
                "latitude": airport["latitude"],
                "longitude": airport["longitude"]
            }
            self.graph[iata] = []
            for route in airport.get("routes", []):
                carriers = [carrier["name"] for carrier in route.get("carriers", [])]
                self.graph[iata].append({
                    "destination": route["iata"],
                    "km": route["km"],
                    "min": route["min"],
                    "carriers": carriers
                })
    
    def add_airport(self, iata, name, country, country_code, latitude, longitude):
        if iata not in self.graph:
            self.graph[iata] = []
            self.airport_info[iata] = {
                "name": name,
                "country": country,
                "country_code": country_code,
                "latitude": latitude,
                "longitude": longitude
            }
    
    def add_route(self, from_iata, to_iata, km, minutes, carriers):
        if from_iata in self.graph:
            self.graph[from_iata].append({
                "destination": to_iata,
                "km": km,
                "min": minutes,
                "carriers": carriers
            })
        else:
            self.graph[from_iata] = [{
                "destination": to_iata,
                "km": km,
                "min": minutes,
                "carriers": carriers
            }]
    
    def get_routes(self, iata):
        return self.graph.get(iata, [])
    
    def get_airport_info(self, iata):
        return self.airport_info.get(iata, {})

    def get_neighboring_airports(self, iata, max_distance=500):
        src_info = self.get_airport_info(iata)
        if not src_info:
            return []  

        src_lat = src_info["latitude"]
        src_lon = src_info["longitude"]
        src_country_code = src_info["country_code"]
        neighbors = []

        for airport, info in self.airport_info.items():
            if airport == iata:
                continue  

            if info["country_code"] != src_country_code:
                continue

            dest_lat = info["latitude"]
            dest_lon = info["longitude"]
            distance = self.calculate_distance(src_lat, src_lon, dest_lat, dest_lon)

            if distance <= max_distance:
                neighbors.append(airport)

        return neighbors
    
    def display_graph(self):
        for airport, routes in self.graph.items():
            info = self.airport_info[airport]
            print(f"{airport} ({info['name']}, {info['country']}, {info['country_code']}, {info['latitude']}, {info['longitude']})")
            for route in routes:
                print(f"  -> {route['destination']} ({', '.join(route['carriers'])}) - {route['km']} km, {route['min']} min")