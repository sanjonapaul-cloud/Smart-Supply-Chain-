const configuredBaseUrl = document.querySelector('meta[name="api-base-url"]')?.content?.trim();

const API_BASE_URLS = [
  configuredBaseUrl,
  'http://localhost:5000',
  'http://127.0.0.1:5000'
].filter((value, index, array) => Boolean(value) && array.indexOf(value) === index);

const ROUTE_HISTORY_KEY = 'routeHistory';
const ROUTE_HISTORY_LIMIT = 10;

const state = {
  map: null,
  mapSourceMarker: null,
  mapDestinationMarker: null,
  routeLine: null,
  speedChart: null,
  isLoading: false
};

const sourceMarkerIcon = L.divIcon({
  className: 'source-pin',
  html: '<div class="source-marker"></div>',
  iconSize: [14, 14],
  iconAnchor: [7, 7]
});

const destinationMarkerIcon = L.divIcon({
  className: 'destination-pin',
  html: '<div class="destination-marker"></div>',
  iconSize: [14, 14],
  iconAnchor: [7, 7]
});

function setMapLoading(isLoading) {
  const loadingNode = document.getElementById('mapLoading');
  if (!loadingNode) {
    return;
  }

  if (isLoading) {
    loadingNode.classList.add('show');
    return;
  }

  loadingNode.classList.remove('show');
}

function setAnalyzeButtonLoading(isLoading) {
  const button = document.getElementById('analyzeBtn');
  if (!button) {
    return;
  }

  state.isLoading = Boolean(isLoading);
  button.disabled = state.isLoading;
  button.textContent = state.isLoading ? 'Analyzing...' : 'Analyze Route';
}

function toNumber(value, fallback = null) {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}

function setMessage(text, type = 'info') {
  const messageNode = document.getElementById('statusMessage');
  if (!messageNode) {
    return;
  }

  if (!text) {
    messageNode.className = 'status-message';
    messageNode.textContent = '';
    return;
  }

  messageNode.className = `status-message show ${type}`;
  messageNode.textContent = text;
}

async function parseJsonSafely(response) {
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    const text = await response.text();
    throw new Error(`API returned non-JSON response: ${text.slice(0, 120)}`);
  }

  return response.json();
}

async function getCoordinates(placeName) {
  const query = String(placeName || '').trim();
  if (!query) {
    throw new Error('Location not found');
  }

  const url = `https://nominatim.openstreetmap.org/search?format=json&limit=1&q=${encodeURIComponent(query)}`;
  const response = await fetch(url, {
    headers: {
      'Accept': 'application/json'
    }
  });

  if (!response.ok) {
    throw new Error('Unable to fetch route data');
  }

  const results = await response.json();
  if (!Array.isArray(results) || !results.length) {
    throw new Error('Location not found');
  }

  const first = results[0];
  const lon = Number(first.lon);
  const lat = Number(first.lat);

  if (!Number.isFinite(lon) || !Number.isFinite(lat)) {
    throw new Error('Location not found');
  }

  return [lon, lat];
}

async function requestRouteAnalysis(payload) {
  let lastError = new Error('Route analysis service unavailable');

  for (const baseUrl of API_BASE_URLS) {
    try {
      const response = await fetch(`${baseUrl}/route-analysis`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await parseJsonSafely(response);

      if (!response.ok) {
        if (data && typeof data === 'object' && data.distance && data.traffic && data.weather) {
          return data;
        }

        lastError = new Error(data?.message || `Route analysis failed: ${response.status}`);
        continue;
      }

      return data;
    } catch (error) {
      lastError = error;
    }
  }

  throw lastError;
}

function getRiskClass(riskLevel) {
  const level = String(riskLevel || '').toLowerCase();
  if (level === 'high') {
    return 'high';
  }
  if (level === 'moderate') {
    return 'moderate';
  }
  return 'low';
}

function readRouteHistory() {
  try {
    const raw = localStorage.getItem(ROUTE_HISTORY_KEY);
    if (!raw) {
      return [];
    }

    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeRouteHistory(history) {
  try {
    localStorage.setItem(ROUTE_HISTORY_KEY, JSON.stringify(history));
  } catch {
    setMessage('Unable to save route history locally.', 'warn');
  }
}

function formatHistoryTime(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return '-';
  }

  return date.toLocaleString([], {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}

function saveRouteHistory(entry) {
  const currentHistory = readRouteHistory();
  const nextHistory = [entry, ...currentHistory].slice(0, ROUTE_HISTORY_LIMIT);
  writeRouteHistory(nextHistory);
  renderRouteHistory();
}

function renderRouteHistory() {
  const list = document.getElementById('historyList');
  if (!list) {
    return;
  }

  const history = readRouteHistory();
  if (!history.length) {
    list.innerHTML = '<div class="history-empty">No recent routes</div>';
    return;
  }

  list.innerHTML = history.map((item, index) => {
    const riskClass = getRiskClass(item.risk || 'Low');
    const source = String(item.source || '-');
    const destination = String(item.destination || '-');
    const distance = Number.isFinite(Number(item.distance)) ? Number(item.distance).toFixed(2) : '0.00';
    const duration = Number.isFinite(Number(item.duration)) ? Number(item.duration).toFixed(2) : '0.00';

    return `
      <button type="button" class="history-item" data-history-index="${index}" title="Load this route and run analysis">
        <div>
          <div class="history-route">${source} -> ${destination}</div>
          <span class="history-meta">Distance: ${distance} km | Duration: ${duration} min</span>
        </div>
        <span class="history-risk ${riskClass}">${item.risk || 'Low'}</span>
        <div class="history-time">${formatHistoryTime(item.timestamp)}</div>
      </button>
    `;
  }).join('');
}

function clearRouteHistory() {
  localStorage.removeItem(ROUTE_HISTORY_KEY);
  renderRouteHistory();
  setMessage('Route history cleared.', 'info');
}

async function handleHistorySelection(event) {
  const target = event.target.closest('[data-history-index]');
  if (!target) {
    return;
  }

  const index = Number(target.getAttribute('data-history-index'));
  if (!Number.isFinite(index)) {
    return;
  }

  const history = readRouteHistory();
  const selected = history[index];
  if (!selected) {
    return;
  }

  const sourceInput = document.getElementById('sourcePlace');
  const destinationInput = document.getElementById('destinationPlace');
  if (!sourceInput || !destinationInput) {
    return;
  }

  sourceInput.value = selected.source || '';
  destinationInput.value = selected.destination || '';

  const form = document.getElementById('routeAnalysisForm');
  if (form && !state.isLoading) {
    form.requestSubmit();
  }
}

function updateCards(data) {
  const distance = data.distance || {};
  const traffic = data.traffic || {};
  const weather = data.weather || {};

  const distanceKm = toNumber(distance.distance_km, 0);
  const durationMin = toNumber(distance.duration_min, 0);

  const currentSpeed = toNumber(traffic.current_speed, 0);
  const freeFlowSpeed = toNumber(traffic.free_flow_speed, 0);

  const condition = weather.condition || 'Unavailable';
  const temp = weather.temperature_celsius;
  const wind = weather.wind_speed_mps;

  document.getElementById('distanceValue').textContent = `${distanceKm.toFixed(2)} km`;
  document.getElementById('durationValue').textContent = `Duration: ${durationMin.toFixed(2)} min`;

  document.getElementById('trafficValue').textContent = traffic.congestion_level || 'Unknown';
  document.getElementById('speedValue').textContent = `Current: ${currentSpeed} | Free Flow: ${freeFlowSpeed}`;

  document.getElementById('weatherCondition').textContent = condition;
  document.getElementById('weatherDetails').textContent = `Temp: ${temp ?? '-'} C | Wind: ${wind ?? '-'} m/s`;

  const riskLevel = data.risk_level || 'Moderate';
  const modelType = String(data.model || 'fallback').toLowerCase();
  const riskCard = document.getElementById('riskCard');
  riskCard.classList.remove('low', 'moderate', 'high');
  riskCard.classList.add(getRiskClass(riskLevel));

  document.getElementById('riskValue').textContent = riskLevel;
  document.getElementById('riskStatus').textContent = `Status: ${data.status || 'unknown'} | Model: ${modelType === 'ml' ? 'ML Prediction' : 'Fallback Rules'}`;
}

function initMap() {
  if (state.map) {
    return;
  }

  state.map = L.map('routeMap', {
    zoomControl: true
  }).setView([22.57, 88.36], 5);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(state.map);
}

function updateMap(sourceCoords, destinationCoords, routePath = []) {
  initMap();

  const sourceLatLng = [sourceCoords[1], sourceCoords[0]];
  const destinationLatLng = [destinationCoords[1], destinationCoords[0]];

  if (state.mapSourceMarker) {
    state.map.removeLayer(state.mapSourceMarker);
  }
  if (state.mapDestinationMarker) {
    state.map.removeLayer(state.mapDestinationMarker);
  }
  if (state.routeLine) {
    state.map.removeLayer(state.routeLine);
  }

  state.mapSourceMarker = L.marker(sourceLatLng, { icon: sourceMarkerIcon }).addTo(state.map).bindPopup('Source');
  state.mapDestinationMarker = L.marker(destinationLatLng, { icon: destinationMarkerIcon }).addTo(state.map).bindPopup('Destination');

  const normalizedRoutePath = Array.isArray(routePath)
    ? routePath
      .filter((point) => Array.isArray(point) && point.length >= 2)
      .map((point) => [point[1], point[0]])
    : [];

  if (normalizedRoutePath.length >= 2) {
    state.routeLine = L.polyline(normalizedRoutePath, {
      color: '#2f7bff',
      weight: 5,
      opacity: 0.92
    }).addTo(state.map);
  } else {
    state.routeLine = L.polyline([sourceLatLng, destinationLatLng], {
      color: '#f3a01f',
      weight: 4,
      opacity: 0.85,
      dashArray: '10 8'
    }).addTo(state.map);

    setMessage('Detailed route unavailable. Showing straight fallback line.', 'warn');
  }

  state.map.fitBounds(state.routeLine.getBounds(), {
    padding: [30, 30]
  });
}

function updateSpeedChart(data) {
  const traffic = data.traffic || {};
  const currentSpeed = toNumber(traffic.current_speed, 0);
  const freeFlowSpeed = toNumber(traffic.free_flow_speed, 0);

  const canvas = document.getElementById('speedChart');
  if (!canvas || typeof Chart === 'undefined') {
    return;
  }

  if (state.speedChart) {
    state.speedChart.destroy();
  }

  state.speedChart = new Chart(canvas.getContext('2d'), {
    type: 'bar',
    data: {
      labels: ['Current Speed', 'Free Flow Speed'],
      datasets: [
        {
          label: 'Speed',
          data: [currentSpeed, freeFlowSpeed],
          backgroundColor: ['#f59e0b', '#22c55e'],
          borderRadius: 10
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            color: '#d6e3ef'
          },
          grid: {
            color: 'rgba(155, 178, 196, 0.2)'
          }
        },
        x: {
          ticks: {
            color: '#d6e3ef'
          },
          grid: {
            color: 'rgba(155, 178, 196, 0.08)'
          }
        }
      }
    }
  });
}

function getFormPayload() {
  const sourcePlace = (document.getElementById('sourcePlace').value || '').trim();
  const destinationPlace = (document.getElementById('destinationPlace').value || '').trim();

  if (!sourcePlace || !destinationPlace) {
    throw new Error('Location not found');
  }

  return {
    sourcePlace,
    destinationPlace
  };
}

function handleStatusMessage(apiResponse) {
  const responseStatus = String(apiResponse.status || '').toLowerCase();
  const errors = Array.isArray(apiResponse.errors) ? apiResponse.errors.filter(Boolean) : [];

  if (responseStatus === 'success' && !errors.length) {
    setMessage('Route analyzed successfully.', 'info');
    return;
  }

  if (responseStatus === 'fallback' || errors.length) {
    const details = errors.length ? ` Details: ${errors.join(' | ')}` : '';
    setMessage(`Some data unavailable, showing best estimate.${details}`, 'warn');
    return;
  }

  setMessage('Some services are unavailable. Displaying fallback values.', 'error');
}

async function onAnalyzeRoute(event) {
  event.preventDefault();

  setMessage('Resolving locations and analyzing route...', 'info');
  setMapLoading(true);
  setAnalyzeButtonLoading(true);

  try {
    const placePayload = getFormPayload();
    const [sourceCoords, destinationCoords] = await Promise.all([
      getCoordinates(placePayload.sourcePlace),
      getCoordinates(placePayload.destinationPlace)
    ]);

    const payload = {
      source: sourceCoords,
      destination: destinationCoords,
      city: placePayload.sourcePlace
    };

    const analysis = await requestRouteAnalysis(payload);

    updateCards(analysis);
    updateMap(sourceCoords, destinationCoords, analysis.route_path || analysis.distance?.route_path || []);
    updateSpeedChart(analysis);
    handleStatusMessage(analysis);

    const responseStatus = String(analysis.status || '').toLowerCase();
    if (responseStatus !== 'error') {
      saveRouteHistory({
        source: placePayload.sourcePlace,
        destination: placePayload.destinationPlace,
        risk: analysis.risk_level || 'Moderate',
        distance: analysis.distance?.distance_km ?? 0,
        duration: analysis.distance?.duration_min ?? 0,
        timestamp: new Date().toISOString()
      });
    }
  } catch (error) {
    const raw = String(error?.message || '');
    if (raw.toLowerCase().includes('location not found')) {
      setMessage('Location not found', 'error');
    } else {
      setMessage('Unable to fetch route data', 'error');
    }
  } finally {
    setMapLoading(false);
    setAnalyzeButtonLoading(false);
  }
}

function initialize() {
  const form = document.getElementById('routeAnalysisForm');
  const clearButton = document.getElementById('clearHistoryBtn');
  const historyList = document.getElementById('historyList');

  if (form) {
    form.addEventListener('submit', onAnalyzeRoute);
  }

  if (clearButton) {
    clearButton.addEventListener('click', clearRouteHistory);
  }

  if (historyList) {
    historyList.addEventListener('click', handleHistorySelection);
  }

  initMap();
  renderRouteHistory();
}

document.addEventListener('DOMContentLoaded', initialize);
