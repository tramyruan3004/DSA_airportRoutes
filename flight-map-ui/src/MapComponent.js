// ✅ Final fix: Preserve departure/destination markers after route plotting
import React, { useEffect, useRef } from 'react';
import * as maptilersdk from '@maptiler/sdk';
import '@maptiler/sdk/dist/maptiler-sdk.css';

const MapComponent = ({ routes, departure, destination, fullRoutes }) => {
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

  useEffect(() => {
    if (!Object.keys(airportDataRef.current).length || !map.current) return;
    if (departure?.value && destination?.value) {
      const depCont = airportDataRef.current[departure.value]?.continent;
      const destCont = airportDataRef.current[destination.value]?.continent;
      const sameContinent = depCont && destCont && depCont === destCont;
      const projectionMode = sameContinent ? 'mercator' : 'globe';

      const adjustMap = () => {
        map.current.setProjection(projectionMode);
        drawBaseMarkers();
        const depCoord = getAirportPosition(departure.value);
        const destCoord = getAirportPosition(destination.value);

        if (isValidCoord(depCoord) && isValidCoord(destCoord)) {
          const bounds = new maptilersdk.LngLatBounds();
          bounds.extend(depCoord);
          bounds.extend(destCoord);
          map.current.fitBounds(bounds, { padding: 60, duration: 1000 });
        }
      };

      if (!map.current.isStyleLoaded()) {
        map.current.once('style.load', adjustMap);
      } else {
        adjustMap();
      }
    }
  }, [departure, destination]);

  useEffect(() => {
    if (!routes || !Object.keys(airportDataRef.current).length || !map.current) return;
    const draw = () => {
      clearAllMarkers();
      drawRoutes(routes);
      drawBaseMarkers();

      if (routes.length > 0) {
        const routePath = Array.isArray(routes[0]?.path) ? routes[0].path : Array.isArray(routes[0]?.[0]) ? routes[0][0] : [];
        const coordinates = routePath.map(getAirportPosition).filter(isValidCoord);
        if (coordinates.length >= 2) {
          const bounds = new maptilersdk.LngLatBounds();
          coordinates.forEach(coord => bounds.extend(coord));
          map.current.fitBounds(bounds, { padding: 60, duration: 1000 });
        }
      }
    };

    if (!map.current.isStyleLoaded()) {
      map.current.once('load', draw);
    } else {
      draw();
    }
  }, [routes]);

  const isValidCoord = (coord) => Array.isArray(coord) && coord.length === 2 && !isNaN(coord[0]) && !isNaN(coord[1]);

  const getAirportPosition = (iata) => {
    const airport = airportDataRef.current[iata];
    if (!airport || airport.longitude == null || airport.latitude == null) {
      console.warn(`⚠ Missing or invalid airport data for IATA: ${iata}`);
      return null;
    }
    const lon = parseFloat(airport.longitude);
    const lat = parseFloat(airport.latitude);
    if (isNaN(lon) || isNaN(lat)) return null;
    return [lon, lat];
  };

  const clearAllMarkers = () => {
    markerRefs.current.forEach(marker => marker.remove());
    markerRefs.current = [];
  };

  const drawBaseMarkers = () => {
    const baseCodes = [departure?.value, destination?.value].filter(Boolean);
    baseCodes.forEach(iata => {
      const coord = getAirportPosition(iata);
      if (isValidCoord(coord)) {
        const marker = new maptilersdk.Marker({ color: '#722f37' })
          .setLngLat(coord)
          .setPopup(new maptilersdk.Popup().setText(iata))
          .addTo(map.current);
        markerRefs.current.push(marker);
      }
    });
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
      const routePath = Array.isArray(route?.path) ? route.path : Array.isArray(route?.[0]) && Array.isArray(route?.[0][0]) ? route[0][0] : Array.isArray(route?.[0]) ? route[0] : [];
      const coordinates = routePath.map(getAirportPosition);
      const validCoords = coordinates.filter(isValidCoord);
      if (validCoords.length < 2) return;

      if (map.current.getSource(`route-${idx}`)) map.current.removeSource(`route-${idx}`);
      map.current.addSource(`route-${idx}`, {
        type: 'geojson',
        data: {
          type: 'Feature',
          geometry: {
            type: 'LineString',
            coordinates: validCoords,
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
          'line-color': '#003366',
          'line-width': 3,
          'line-opacity': 0.9,
          'line-dasharray': [2, 4],
        },
      });

      routePath.forEach((iata, i) => {
        const coord = coordinates[i];
        if (!isValidCoord(coord)) return;
        const isEdge = i === 0 || i === routePath.length - 1;
        const color = isEdge ? '#722f37' : '#ffaa00';

        const marker = new maptilersdk.Marker({ color })
          .setLngLat(coord)
          .setPopup(new maptilersdk.Popup().setText(iata))
          .addTo(map.current);
        markerRefs.current.push(marker);

        if (!isEdge) {
          clusterFeatures.push({
            type: 'Feature',
            geometry: { type: 'Point', coordinates: coord },
            properties: { iata },
          });
        }
      });
    });

    if (clusterFeatures.length) {
      if (map.current.getSource(middleClusterLayerId)) map.current.removeSource(middleClusterLayerId);
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

  return (
    <div
      ref={mapContainer}
      className="map-container"
      style={{ height: '97vh', width: '100%', margin: 0, padding: 0, overflow: 'hidden', borderRadius: '10px', background: 'linear-gradient(to bottom right, #0d0d0d, #1a1a1a)' }}
    />
  );
};

export default MapComponent;
