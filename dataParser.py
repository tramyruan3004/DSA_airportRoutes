import json

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

    def get_distance(self, dep_code, dest_code):
        for route in self.get_routes(dep_code):
            if route["destination"] == dest_code:
                return route["km"]
        return float('inf')
    
    def get_airport_info(self, iata):
        return self.airport_info.get(iata, {})
    
    def display_graph(self):
        for airport, routes in self.graph.items():
            info = self.airport_info[airport]
            print(f"{airport} ({info['name']}, {info['country']}, {info['country_code']}, {info['latitude']}, {info['longitude']})")
            for route in routes:
                print(f"  -> {route['destination']} ({', '.join(route['carriers'])}) - {route['km']} km, {route['min']} min")
