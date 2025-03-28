import React, { useState, useEffect, useCallback } from 'react';
import './App.css';
import Select from 'react-select';
import MapComponent from './MapComponent';
import { loadAirportOptions } from './utils/airportsList';

const App = () => {
  const [mode, setMode] = useState('complete');
  const [tripType, setTripType] = useState('oneway');
  const [airportOptions, setAirportOptions] = useState([]);
  const [departure, setDeparture] = useState(null);
  const [destination, setDestination] = useState(null);
  const [middle, setMiddle] = useState(null);
  const [searchStarted, setSearchStarted] = useState(false);
  const [cabin, setCabin] = useState('Economy');
  const [currency, setCurrency] = useState('SGD');
  const [currencyRates, setCurrencyRates] = useState({});
  const [routeType, setRouteType] = useState('cheapest');
  const [stopFilters, setStopFilters] = useState({ direct: true, oneStop: true, twoStop: true });
  const [foundRoutes, setFoundRoutes] = useState([]);
  const [currentPage, setCurrentPage] = useState(0);
  const [selectedRoute, setSelectedRoute] = useState(null);
  const resultsPerPage = 30;

  const fetchRoutes = useCallback(async () => {
    if (!departure || !destination) return;
    let query = `departure=${departure.value}&destination=${destination.value}&stops=2&cabin=${cabin}&tripType=${tripType}&routeType=${routeType}&mode=${mode}&currency=${currency}`;
    if (tripType === 'multicity' && middle) {
      query += `&middle=${middle.value}`;
    }
    try {
      const response = await fetch(`http://localhost:5000/routes?${query}`);
      const data = await response.json();
      if (Array.isArray(data)) {
        setFoundRoutes(data);
        setCurrentPage(0);
        setSelectedRoute(null);
      } else {
        setFoundRoutes([]);
      }
      setSearchStarted(true);
    } catch (err) {
      console.error('Error fetching routes:', err);
      setFoundRoutes([]);
    }
  }, [departure, destination, cabin, tripType, routeType, mode, currency, middle]);

  const handleSearch = () => {
    fetchRoutes();
  };

  useEffect(() => {
    const fetchAirports = async () => {
      const options = await loadAirportOptions();
      setAirportOptions(options);
    };
    fetchAirports();
  }, []);

  useEffect(() => {
    const fetchCurrencyData = async () => {
      try {
        const res = await fetch('/currency.json');
        const data = await res.json();
        setCurrencyRates(data.rates || {});
      } catch (err) {
        console.error('Error loading currency data:', err);
      }
    };
    fetchCurrencyData();
  }, []);


  const handleStopFilterChange = (type) => {
    setStopFilters(prev => ({ ...prev, [type]: !prev[type] }));
    setSelectedRoute(null);
  };

  const getStopCount = (pathLength) => {
    return tripType === 'multicity' ? pathLength - 3 : pathLength - 2;
  };

  const sortRoutes = (routes) => {
    const direct = routes.filter(r => getStopCount(r.path.length) === 0);
    const others = routes.filter(r => getStopCount(r.path.length) !== 0);
    const sortFn = routeType === 'cheapest'
      ? (a, b) => a.price - b.price
      : (a, b) => a.duration - b.duration;
    return [...direct.sort(sortFn), ...others.sort(sortFn)];
  };

  const filteredRoutes = Array.isArray(foundRoutes)
    ? sortRoutes(
      foundRoutes.filter(route => {
        const stops = getStopCount(route.path.length);
        return (stops === 0 && stopFilters.direct) ||
          (stops === 1 && stopFilters.oneStop) ||
          (stops === 2 && stopFilters.twoStop);
      })
    )
    : [];

  const paginatedRoutes = filteredRoutes.slice(
    currentPage * resultsPerPage,
    (currentPage + 1) * resultsPerPage
  );

  const totalPages = Math.ceil(filteredRoutes.length / resultsPerPage);

  const handleRouteSelection = (route) => {
    setSelectedRoute(route);
  };

  useEffect(() => {
    if (searchStarted) {
      fetchRoutes();
    }
  }, [routeType, cabin, currency, searchStarted, fetchRoutes]);

  return (
    <div className="app-container">
      {!searchStarted ? (
        <div className="hero-section">
          <div className="hero-overlay" />
          <div className="hero-content">
            <h1 className="hero-title">SEARCH BEST FLIGHTS</h1>
            <p className="hero-subtitle">Experience a smooth and smart flight search journey</p>

            <div className="mode-navbar">
              <button className={mode === 'complete' ? 'nav-tab active' : 'nav-tab'} onClick={() => setMode('complete')}>Complete (BFS)</button>
              <button className={mode === 'quick' ? 'nav-tab active' : 'nav-tab'} onClick={() => setMode('quick')}>Quick (Dijkstra & A*)</button>
            </div>

            <div className="search-form-container">
              <h2>Start Your Journey</h2>
              <div className="trip-toggle-group">
                <button className={tripType === 'oneway' ? 'toggle-btn active' : 'toggle-btn'} onClick={() => setTripType('oneway')}>One-Way</button>
                <button className={tripType === 'multicity' ? 'toggle-btn active' : 'toggle-btn'} onClick={() => setTripType('multicity')}>Multi-City</button>
              </div>
              <div className="input-group">
                <div className="select-label">Departure Airport</div>
                <Select classNamePrefix="react-select" options={airportOptions} value={departure} onChange={setDeparture} placeholder="Select departure..." />
              </div>
              <div className="input-group">
                <div className="select-label">Destination Airport</div>
                <Select classNamePrefix="react-select" options={airportOptions} value={destination} onChange={setDestination} placeholder="Select destination..." />
              </div>
              {tripType === 'multicity' && (
                <div className="input-group">
                  <div className="select-label">Middle Airport</div>
                  <Select classNamePrefix="react-select" options={airportOptions} value={middle} onChange={setMiddle} placeholder="Select middle airport..." />
                </div>
              )}
              <button
                className="primary-btn"
                onClick={handleSearch}
                disabled={
                  !departure || !destination || (tripType === 'multicity' && !middle)
                }
              >
                Search Flights
              </button>

            </div>
          </div>
        </div>
      ) : (
        <main className="results-section">
          <div className="results-overlay" />
          <div className="results-content">
            <div className="results-sidebar">
              <div className="flight-info">
                <h2>Flight Information</h2>
                <div className="mode-switch">
                  <span className={mode === 'complete' ? 'mode-btn active' : 'mode-btn'}>Complete</span>
                  <span className={mode === 'quick' ? 'mode-btn active' : 'mode-btn'}>Quick</span>
                </div>
                <div className="input-pair">
                  <div><label>From</label><input className="mini-input" type="text" value={departure?.label || ''} readOnly /></div>
                  <div><label>To</label><input className="mini-input" type="text" value={destination?.label || ''} readOnly /></div>
                </div>
                {tripType === 'multicity' && (
                  <div className="input-extra">
                    <div><label>Middle</label><input className="mini-input" type="text" value={middle?.label || ''} readOnly /></div>
                  </div>
                )}
                <div className="filter-group">
                  <label>Route Type:</label>
                  <div className="route-toggle-group">
                    <button className={routeType === 'cheapest' ? 'toggle-btn active' : 'toggle-btn'} onClick={() => setRouteType('cheapest')}>Cheapest</button>
                    <button className={routeType === 'fastest' ? 'toggle-btn active' : 'toggle-btn'} onClick={() => setRouteType('fastest')}>Fastest</button>
                  </div>
                </div>
                <div className="filters-row">
                  <div className="filter-left-col">
                    <div className="filter-half">
                      <label>Cabin Type:</label>
                      <select className="mini-input" value={cabin} onChange={(e) => setCabin(e.target.value)}>
                        <option>Economy</option>
                        <option>Premium Economy</option>
                        <option>Business</option>
                        <option>First</option>
                      </select>
                    </div>
                    <div className="filter-half">
                      <label>Currency:</label>
                      <select className="mini-input" value={currency} onChange={(e) => setCurrency(e.target.value)}>
                        {Object.entries(currencyRates).map(([code, val]) => (
                          <option key={code} value={code}>{val.name} ({code})</option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <div className="filter-half">
                    <label>Stops:</label>
                    <div className="stop-filters">
                      <label><input type="checkbox" checked={stopFilters.direct} onChange={() => handleStopFilterChange('direct')} /> Direct</label>
                      <label><input type="checkbox" checked={stopFilters.oneStop} onChange={() => handleStopFilterChange('oneStop')} /> 1-Stop</label>
                      <label><input type="checkbox" checked={stopFilters.twoStop} onChange={() => handleStopFilterChange('twoStop')} /> 2-Stop</label>
                    </div>
                  </div>
                </div>
                <h3 className="result-title">Results</h3>
                {paginatedRoutes.length === 0 ? (
                  <p>No routes found matching current filters.</p>
                ) : (
                  paginatedRoutes.map((route, idx) => (
                    <div className="flight-card" key={idx}>
                      <div className="route-line">
                        {route.path.join(' ✈ ')}
                      </div>
                      <div className="flight-details">
                        {route.routeLabel && <p><strong> {route.routeLabel}</strong></p>}
                        <p><strong>Distance:</strong> {route.distance} km</p>
                        <p><strong>Duration:</strong> {Math.floor(route.duration / 60)}h {route.duration % 60}m</p>
                        <div className="price-btn-row">
                           <p><strong>Price:</strong> {route.symbol || '$'}{route.price?.toFixed(2)}</p>
                             <button className="more-btn" onClick={() => handleRouteSelection(route)}>Show routes →</button>
                        </div>
                        {route.distance_to_destination !== undefined && (
                        <p><strong>Distance from {route.path[1]} to {destination?.value}:</strong> {route.distance_to_destination} km</p>)}
                      </div>
                    </div>
                  ))
                )}
                {totalPages > 1 && (
                  <div className="pagination-controls pagination-right">
                    <button onClick={() => setCurrentPage(p => Math.max(0, p - 1))} disabled={currentPage === 0}>← Prev</button>
                    <span> Page {currentPage + 1} of {totalPages} </span>
                    <button onClick={() => setCurrentPage(p => Math.min(totalPages - 1, p + 1))} disabled={currentPage >= totalPages - 1}>Next →</button>
                  </div>
                )}
              </div>
              <div><button className="primary-btn" onClick={() => setSearchStarted(false)}>← Back to Home</button></div>
            </div>
            <div className="results-map">
              <MapComponent
                departure={departure}
                destination={destination}
                routes={selectedRoute ? [selectedRoute] : (filteredRoutes.length > 0 ? [filteredRoutes[0]] : [])}
                tripType={tripType}
              />
            </div>
          </div>
        </main>
      )}
      <footer className="footer"><p>© 2025 Flight Search ✈</p></footer>
    </div>
  );
};

export default App;