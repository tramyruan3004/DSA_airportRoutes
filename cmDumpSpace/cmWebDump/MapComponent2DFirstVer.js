import React, { useEffect, useState, useRef } from 'react';
import axios from 'axios';
import * as maptilersdk from '@maptiler/sdk';
import '@maptiler/sdk/dist/maptiler-sdk.css'; // Import MapTiler CSS

const MapComponent = () => {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const [routes, setRoutes] = useState([]);
  const [departure, setDeparture] = useState('AAA');
  const [destination, setDestination] = useState('AAE');
  const [stops, setStops] = useState(0);
  const [cabin, setCabin] = useState('Economy');

  // Initialize the map
  useEffect(() => {
    if (map.current) return; // Stop if the map is already initialized

    map.current = new maptilersdk.Map({
      container: mapContainer.current,
      style: maptilersdk.MapStyle.STREETS, // Use any MapTiler style
      center: [0, 20], // Initial map center
      zoom: 2, // Initial zoom level
      apiKey: 'QDTbVXjPuiGvWKd4gDUW', // Replace with your MapTiler API key
    });

    // Add navigation controls
    map.current.addControl(new maptilersdk.NavigationControl(), 'top-right');
  }, []);

  // Fetch routes when filters change
  useEffect(() => {
    fetchRoutes();
  }, [departure, destination, stops, cabin]);

  const fetchRoutes = async () => {
    try {
      const response = await axios.get(`http://localhost:5000/routes`, {
        params: {
          departure,
          destination,
          stops,
          cabin,
        },
      });
      setRoutes(response.data);
      drawRoutes(response.data);
    } catch (error) {
      console.error('Error fetching routes:', error);
    }
  };

  // Draw routes and markers on the map
  const drawRoutes = (routes) => {
    if (!map.current) return;

    // Clear existing markers and polylines
    map.current.getCanvas().style.cursor = '';
    map.current.getSource('route') && map.current.removeLayer('route');
    map.current.getSource('route') && map.current.removeSource('route');
    map.current.getSource('markers') && map.current.removeLayer('markers');
    map.current.getSource('markers') && map.current.removeSource('markers');

    // Add polylines for each route
    routes.forEach((route, idx) => {
      const coordinates = route[0].map((iata) => getAirportPosition(iata));

      map.current.addSource(`route-${idx}`, {
        type: 'geojson',
        data: {
          type: 'Feature',
          properties: {},
          geometry: {
            type: 'LineString',
            coordinates,
          },
        },
      });

      map.current.addLayer({
        id: `route-${idx}`,
        type: 'line',
        source: `route-${idx}`,
        layout: {
          'line-join': 'round',
          'line-cap': 'round',
        },
        paint: {
          'line-color': '#007cbf',
          'line-width': 2,
        },
      });

      // Add markers for each airport
      coordinates.forEach((coord, i) => {
        new maptilersdk.Marker({ color: '#FF0000' })
          .setLngLat(coord)
          .setPopup(new maptilersdk.Popup().setText(route[0][i]))
          .addTo(map.current);
      });
    });
  };

  // Mock function to get airport positions
  const getAirportPosition = (iata) => {
    const airports = {
      AAA: [-145.50913, -17.355648], // Note: MapTiler uses [lng, lat]
      AAE: [7.811857, 36.821392],
      // Add more airports as needed
    };
    return airports[iata] || [0, 0];
  };

  return (
    <div>
      <div style={{ marginBottom: '20px' }}>
        <label>
          Departure:
          <input
            type="text"
            value={departure}
            onChange={(e) => setDeparture(e.target.value)}
            style={{ marginRight: '10px' }}
          />
        </label>
        <label>
          Destination:
          <input
            type="text"
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
            style={{ marginRight: '10px' }}
          />
        </label>
        <label>
          Stops:
          <input
            type="number"
            value={stops}
            onChange={(e) => setStops(e.target.value)}
            style={{ marginRight: '10px' }}
          />
        </label>
        <label>
          Cabin:
          <select
            value={cabin}
            onChange={(e) => setCabin(e.target.value)}
            style={{ marginRight: '10px' }}
          >
            <option value="Economy">Economy</option>
            <option value="Premium Economy">Premium Economy</option>
            <option value="Business">Business</option>
            <option value="First">First</option>
          </select>
        </label>
        <button onClick={fetchRoutes}>Search</button>
      </div>
      <div ref={mapContainer} style={{ height: '80vh', width: '100%' }} />
    </div>
  );
};

export default MapComponent;