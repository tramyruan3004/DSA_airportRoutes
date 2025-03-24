// ✅ Updated MapComponent.js with animated route lines and clustered stop markers
import React, { useEffect, useRef } from 'react';
import * as maptilersdk from '@maptiler/sdk';
import '@maptiler/sdk/dist/maptiler-sdk.css';

const MapComponent = ({ routes, departure, destination, fullRoutes }) => {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const airportDataRef = useRef({});
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
    if (!airportDataRef.current || !map.current) return;
    if (departure?.value && destination?.value) {
      const depCont = airportDataRef.current[departure.value]?.continent;
      const destCont = airportDataRef.current[destination.value]?.continent;
      const sameContinent = depCont && destCont && depCont === destCont;

      const projectionMode = sameContinent ? 'mercator' : 'globe';
if (!map.current.isStyleLoaded()) {
  map.current.once('style.load', () => {
    map.current.setProjection(projectionMode);
    drawMarkersOnly([departure.value, destination.value]);

      // Adjust map center/zoom
      const depCoord = getAirportPosition(departure.value);
      const destCoord = getAirportPosition(destination.value);
      if (depCoord && destCoord && depCoord[0] !== 0 && destCoord[0] !== 0) {
        const bounds = new maptilersdk.LngLatBounds();
        bounds.extend(depCoord);
        bounds.extend(destCoord);
        map.current.fitBounds(bounds, { padding: 60, duration: 1000 });
      }
  });
} else {
  map.current.setProjection(projectionMode);
  drawMarkersOnly([departure.value, destination.value]);
}
    }
  }, [departure, destination]);

  useEffect(() => {
    if (!routes || !airportDataRef.current || !map.current) return;
    if (!map.current.isStyleLoaded()) {
      map.current.once('load', () => drawRoutes(routes));
    } else {
      drawRoutes(routes);
      if (routes.length > 0) {
        const routePath = Array.isArray(routes[0].path) ? routes[0].path : Array.isArray(routes[0][0]) ? routes[0][0] : [];
        const bounds = new maptilersdk.LngLatBounds();
        routePath.forEach(iata => {
          const coord = getAirportPosition(iata);
          if (coord && coord[0] !== 0) bounds.extend(coord);
        });
        map.current.fitBounds(bounds, { padding: 60, duration: 1000 });
      }
    }
  }, [routes]);

  const getAirportPosition = (iata) => {
    const airport = airportDataRef.current[iata];
    if (!airport) {
      console.warn(`⚠ Missing airport data for IATA: ${iata}`);
      return [0, 0];
    }
    return [parseFloat(airport.longitude), parseFloat(airport.latitude)];
  };

  const drawMarkersOnly = (iataCodes) => {
    clearRouteLayers();
    iataCodes.forEach(iata => {
      const coord = getAirportPosition(iata);
      new maptilersdk.Marker({ color: '#00ff84' })
        .setLngLat(coord)
        .setPopup(new maptilersdk.Popup().setText(iata))
        .addTo(map.current);
    });
  };

  const clearRouteLayers = () => {
    const layers = Object.keys(map.current.style._layers || {});
    layers.forEach((layerId) => {
      if (layerId.startsWith('route-') || layerId === middleClusterLayerId) {
        if (map.current.getLayer(layerId)) map.current.removeLayer(layerId);
        if (map.current.getSource(layerId)) map.current.removeSource(layerId);
      }
    });
  };

  const drawRoutes = (routes) => {
    clearRouteLayers();
    const clusterFeatures = [];
    routes.forEach((route, idx) => {
      const routePath = Array.isArray(route.path) ? route.path : Array.isArray(route[0]) ? route[0] : [];
      if (!Array.isArray(routePath) || routePath.length < 2) return;
      const coordinates = routePath.map(getAirportPosition);

      map.current.addSource(`route-${idx}`, {
        type: 'geojson',
        data: {
          type: 'Feature',
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
          'line-color': '#00ff84',
          'line-width': 3,
          'line-opacity': 0.9,
          'line-dasharray': [2, 4],
        },
      });

      routePath.forEach((iata, i) => {
        const coord = coordinates[i];
        const color = i === 0 || i === route[0].length - 1 ? '#00ff84' : '#ffcc00';

        // Cluster only middle airports
        if (i > 0 && i < route[0].length - 1) {
          clusterFeatures.push({
            type: 'Feature',
            geometry: { type: 'Point', coordinates: coord },
            properties: { iata },
          });
        } else {
          new maptilersdk.Marker({ color })
            .setLngLat(coord)
            .setPopup(new maptilersdk.Popup().setText(iata))
            .addTo(map.current);
        }
      });
    });

    if (clusterFeatures.length) {
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
