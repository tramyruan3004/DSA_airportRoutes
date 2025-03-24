from flask import Flask, jsonify, request
from flask_cors import CORS
import algorithms
import dataParser
import json

app = Flask(__name__)
CORS(app)

with open('dataset/airline_routes.json') as f:
    data = json.load(f)

graph = dataParser.AirportGraph(data)

def format_routes(routes):
    formatted = []
    for r in routes:
        if isinstance(r, dict):
            formatted.append(r)
        elif isinstance(r, (tuple, list)) and len(r) >= 4:
            formatted.append({
                "path": r[0],
                "distance": r[1],
                "duration": r[2],
                "price": r[3],
                "cabin": r[4] if len(r) > 4 else None
            })
    return formatted

@app.route('/routes', methods=['GET'])
def get_routes():
    departure = request.args.get('departure')
    destination = request.args.get('destination')
    middle = request.args.get('middle')
    try:
        stops = int(request.args.get('stops', 0))
    except ValueError:
        stops = 2  
    cabin = request.args.get('cabin', 'Economy')
    route_type = request.args.get('routeType', 'cheapest')
    trip_type = request.args.get('tripType', 'oneway')
    mode = request.args.get('mode')
    print("Received Request →", request.args)
    if mode == 'quick':
        if trip_type == 'multicity' and middle:
            routes = algorithms.find_multi_city_flights(graph, departure, middle, destination, stops, route_type, cabin)
        else:
            routes = algorithms.find_one_way_flights_dijkstra(graph, departure, destination, stops, cabin)
    else:
        if trip_type == 'multicity' and middle:
            routes = algorithms.find_multi_city_flights(graph, departure, middle, destination, stops, route_type, cabin)
        else:
            routes = algorithms.find_one_way_flights(graph, departure, destination, stops, cabin)

    formatted_routes = format_routes(routes)
    print("Found Routes →", formatted_routes[:2])

    return jsonify(formatted_routes)

@app.errorhandler(Exception)
def handle_error(e):
    return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
