from flask import Flask, jsonify, request
from flask_cors import CORS
import algorithms
import dataParser
import json

app = Flask(__name__)
CORS(app)

# Load the dataset
with open('dataset/airline_routes.json') as f:
    data = json.load(f)

graph = dataParser.AirportGraph(data)

@app.route('/routes', methods=['GET'])
def get_routes():
    departure = request.args.get('departure')
    destination = request.args.get('destination')
    stops = int(request.args.get('stops', 0))
    cabin = request.args.get('cabin', 'Economy')
    
    routes = algorithms.find_one_way_flights(graph, departure, destination, stops, cabin)
    return jsonify(routes)

if __name__ == '__main__':
    app.run(debug=True)