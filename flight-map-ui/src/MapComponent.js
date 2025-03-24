import React, { useEffect, useRef } from 'react';
import * as maptilersdk from '@maptiler/sdk';
import '@maptiler/sdk/dist/maptiler-sdk.css';

const MapComponent = ({ routes, departure, destination, tripType }) => {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const airportDataRef = useRef({});
  const markerRefs = useRef([]);
  const middleClusterLayerId = 'middle-airport-cluster';

  useEffect(() => {
    if (map.current) return;
    map.current = new maptilersdk.Map({
      container: mapContainer.current,
      style: maptilersdk.MapStyle.STREETS,
      center: [0, 20],
      zoom: 2,
      apiKey: 'QDTbVXjPuiGvWKd4gDUW',
      projection: 'globe',
    });
    map.current.addControl(new maptilersdk.NavigationControl(), 'top-right');
  }, []);

  useEffect(() => {
    const fetchAirportData = async () => {
      try {
        const res = await fetch('/airline_routes.json');
        const data = await res.json();
        airportDataRef.current = data;
      } catch (err) {
        console.error('Error loading airport data:', err);
      }
    };
    fetchAirportData();
  }, []);

  const isValidCoord = (coord) =>
    Array.isArray(coord) && coord.length === 2 && !isNaN(coord[0]) && !isNaN(coord[1]);

  const getAirportPosition = (iata) => {
    const airport = airportDataRef.current[iata];
    if (!airport || airport.longitude == null || airport.latitude == null) return null;
    return [parseFloat(airport.longitude), parseFloat(airport.latitude)];
  };

  const clearAllMarkers = () => {
    markerRefs.current.forEach(marker => marker.remove());
    markerRefs.current = [];
  };

  const clearRouteLayers = () => {
    const layers = Object.keys(map.current.style?._layers || {});
    layers.forEach((layerId) => {
      if (layerId.startsWith('route-') || layerId === middleClusterLayerId || layerId === 'cluster-count') {
        if (map.current.getLayer(layerId)) map.current.removeLayer(layerId);
        if (map.current.getSource(layerId)) map.current.removeSource(layerId);
      }
    });
  };

  const drawRoutes = (routes) => {
    clearRouteLayers();
    const clusterFeatures = [];

    routes.forEach((route, idx) => {
      const routePath = Array.isArray(route?.path) ? route.path : [];
      const coordinates = routePath.map(getAirportPosition);
      const validCoords = coordinates.filter(isValidCoord);
      if (validCoords.length < 2) return;

      map.current.addSource(`route-${idx}`, {
        type: 'geojson',
        data: {
          type: 'Feature',
          geometry: { type: 'LineString', coordinates: validCoords },
        },
      });

      map.current.addLayer({
        id: `route-${idx}`,
        type: 'line',
        source: `route-${idx}`,
        layout: { 'line-join': 'round', 'line-cap': 'round' },
        paint: {
          'line-color': '#003366',
          'line-width': 3,
          'line-opacity': 0.9,
          'line-dasharray': [2, 4],
        },
      });

      const mainStops = [0, routePath.length - 1];
      if (tripType === 'multicity' && routePath.length >= 3) {
        mainStops.splice(1, 0, Math.floor(routePath.length / 2));
      }

      routePath.forEach((iata, i) => {
        const coord = coordinates[i];
        if (!isValidCoord(coord)) return;

        const color = mainStops.includes(i) ? '#ff0000' : '#ffaa00';

        const marker = new maptilersdk.Marker({ color })
          .setLngLat(coord)
          .setPopup(new maptilersdk.Popup().setText(iata))
          .addTo(map.current);
        markerRefs.current.push(marker);

        if (!mainStops.includes(i)) {
          clusterFeatures.push({
            type: 'Feature',
            geometry: { type: 'Point', coordinates: coord },
            properties: { iata },
          });
        }
      });
    });

    if (clusterFeatures.length) {
      if (map.current.getSource(middleClusterLayerId)) {
        if (map.current.getLayer(middleClusterLayerId)) map.current.removeLayer(middleClusterLayerId);
        if (map.current.getLayer('cluster-count')) map.current.removeLayer('cluster-count');
        map.current.removeSource(middleClusterLayerId);
      }

      map.current.addSource(middleClusterLayerId, {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: clusterFeatures },
        cluster: true,
        clusterMaxZoom: 6,
        clusterRadius: 30,
      });

      map.current.addLayer({
        id: middleClusterLayerId,
        type: 'circle',
        source: middleClusterLayerId,
        filter: ['has', 'point_count'],
        paint: {
          'circle-color': '#ffaa00',
          'circle-radius': 16,
          'circle-stroke-width': 1,
          'circle-stroke-color': '#fff',
        },
      });

      map.current.addLayer({
        id: 'cluster-count',
        type: 'symbol',
        source: middleClusterLayerId,
        filter: ['has', 'point_count'],
        layout: {
          'text-field': ['get', 'point_count'],
          'text-font': ['Open Sans Bold'],
          'text-size': 12,
        },
        paint: { 'text-color': '#000' },
      });
    }
  };

  useEffect(() => {
    if (!routes || !map.current || !Object.keys(airportDataRef.current).length) return;

    const routePath = Array.isArray(routes[0]?.path) ? routes[0].path : [];
    const coords = routePath.map(getAirportPosition).filter(isValidCoord);

    const depIATA = routePath[0];
    const destIATA = routePath[routePath.length - 1];

    const depCont = airportDataRef.current[depIATA]?.continent;
    const destCont = airportDataRef.current[destIATA]?.continent;
    const sameContinent = depCont && destCont && depCont === destCont;
    const projectionMode = sameContinent ? 'mercator' : 'globe';
    map.current.setProjection(projectionMode);

    if (coords.length > 0) {
      const bounds = new maptilersdk.LngLatBounds();
      coords.forEach(c => bounds.extend(c));
      map.current.fitBounds(bounds, { padding: 60, duration: 1000 });
    }

    clearAllMarkers();
    drawRoutes(routes);
  }, [routes]);

  return (
    <div
      ref={mapContainer}
      className="map-container"
      style={{
        height: '97vh',
        width: '100%',
        margin: 0,
        padding: 0,
        overflow: 'hidden',
        borderRadius: '10px',
        background: 'linear-gradient(to bottom right, #0d0d0d, #1a1a1a)'
      }}
    />
  );
};

export default MapComponent;
