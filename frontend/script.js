const BASE_URL = document.querySelector('meta[name="api-base-url"]')?.content?.trim() || 'http://localhost:5000';

const state = {
  chart: null,
  latestProbability: null
};

function getRiskState(result) {
  const raw = String(result || '').toLowerCase();
  if (raw.includes('high')) {
    return {
      isHighRisk: true,
      label: 'High Risk',
      icon: 'warning'
    };
  }

  return {
    isHighRisk: false,
    label: 'Low Risk',
    icon: 'check_circle'
  };
}

function toNumber(value, fallback = null) {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}

function safeText(value, fallback = '-') {
  if (value === null || value === undefined) {
    return fallback;
  }

  const text = String(value).trim();
  if (!text || text === '[object HTMLInputElement]') {
    return fallback;
  }

  return text;
}

function formatTimestamp(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return safeText(value, '-');
  }

  return date.toLocaleString([], {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}

async function parseJsonSafely(response, context) {
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    const text = await response.text();
    throw new Error(`${context} expected JSON but received: ${text.slice(0, 120)}`);
  }

  return response.json();
}

async function requestPrediction(payload) {
  const response = await fetch(`${BASE_URL}/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const data = await parseJsonSafely(response, 'Prediction API');
    throw new Error(data.message || `Prediction request failed: ${response.status}`);
  }

  return parseJsonSafely(response, 'Prediction API');
}

async function fetchHistoryData() {
  const response = await fetch(`${BASE_URL}/history`);

  if (!response.ok) {
    const data = await parseJsonSafely(response, 'History API');
    throw new Error(data.message || `History request failed: ${response.status}`);
  }

  return parseJsonSafely(response, 'History API');
}

function normalizeInputValue(value) {
  if (value === null || value === undefined) {
    return '-';
  }

  if (typeof value === 'object') {
    if (typeof value.value === 'string' || typeof value.value === 'number') {
      return value.value;
    }
    return '-';
  }

  const text = String(value).trim();
  return text && text !== '[object HTMLInputElement]' ? text : '-';
}

function getHistoryField(item, key) {
  const input = item?.input;
  if (input && typeof input === 'object' && input[key] !== undefined) {
    return input[key];
  }

  if (item && item[key] !== undefined) {
    return item[key];
  }

  return undefined;
}

function createHistoryRow(item) {
  const distanceValue = normalizeInputValue(getHistoryField(item, 'distance'));
  const delayValue = normalizeInputValue(getHistoryField(item, 'delay'));
  const weatherValue = normalizeInputValue(getHistoryField(item, 'weather'));

  const weatherNormalized = String(weatherValue).trim().toLowerCase();
  const weatherLabel =
    weatherNormalized === '2' || weatherNormalized === 'bad'
      ? 'Bad'
      : weatherNormalized === '1' || weatherNormalized === 'moderate'
        ? 'Moderate'
        : 'Good';

  const risk = getRiskState(item.result);
  const row = document.createElement('tr');
  row.className = 'transition-all duration-150 hover:bg-gradient-to-r hover:from-blue-50/50 hover:to-transparent';
  row.innerHTML = `
    <td class="py-3 sm:py-4 px-3 sm:px-5 text-[12px] sm:text-[13px] text-slate-700 whitespace-nowrap font-medium">${formatTimestamp(item.timestamp)}</td>
    <td class="py-3 sm:py-4 px-3 sm:px-5 text-[12px] sm:text-[13px] text-slate-800 font-medium">${distanceValue === '-' ? '<span class="text-slate-400">-</span>' : `<span class="text-[#004ac6] font-semibold">${distanceValue}</span> km`}</td>
    <td class="py-3 sm:py-4 px-3 sm:px-5 text-[12px] sm:text-[13px] text-slate-800 font-medium">${delayValue === '-' ? '<span class="text-slate-400">-</span>' : `<span class="text-[#004ac6] font-semibold">${delayValue}</span> hrs`}</td>
    <td class="py-3 sm:py-4 px-3 sm:px-5 text-center text-[12px] sm:text-[13px]">
      <span class="inline-block px-2 sm:px-3 py-1 rounded-full bg-slate-100 text-slate-700 text-[11px] sm:text-[12px] font-medium whitespace-nowrap">${weatherLabel}</span>
    </td>
    <td class="py-3 sm:py-4 px-3 sm:px-5 text-center">
      <span class="inline-flex items-center gap-1 sm:gap-1.5 px-2 sm:px-3 py-1 sm:py-1.5 rounded-full text-[11px] sm:text-[12px] font-bold whitespace-nowrap ${
        risk.isHighRisk 
          ? 'bg-red-100/80 text-red-700 border border-red-200' 
          : 'bg-green-100/80 text-green-700 border border-green-200'
      }">
        <span class="material-symbols-outlined text-[13px] sm:text-[14px] flex-shrink-0">${risk.icon}</span>
        <span>${risk.label}</span>
      </span>
    </td>
  `;

  return row;
}

function appendHistoryRow(item, tableElement) {
  if (!tableElement) {
    return;
  }

  const emptyRow = tableElement.querySelector('.empty-state');
  if (emptyRow) {
    tableElement.innerHTML = '';
  }

  const row = createHistoryRow(item);
  tableElement.prepend(row);
}

function renderHistoryTable(entries, tableElement) {
  tableElement.innerHTML = '';

  if (!entries.length) {
    tableElement.innerHTML = `
      <tr>
        <td colspan="5" class="empty-state">
          <p>No predictions yet. Run a risk analysis to populate the ledger.</p>
        </td>
      </tr>
    `;
    return;
  }

  entries.forEach((item) => {
    tableElement.appendChild(createHistoryRow(item));
  });
}

function renderRiskChart(entries, canvas, riskProbability = null) {
  if (!canvas || typeof Chart === 'undefined') {
    return;
  }

  let safe = 0;
  let high = 0;

  if (riskProbability && Number.isFinite(Number(riskProbability.safe)) && Number.isFinite(Number(riskProbability.high_risk))) {
    safe = Number(riskProbability.safe);
    high = Number(riskProbability.high_risk);
    state.latestProbability = riskProbability;
  } else {
    entries.forEach((item) => {
      if (String(item.result).includes('High')) {
        high += 1;
      } else {
        safe += 1;
      }
    });
    state.latestProbability = null;
  }

  const ctx = canvas.getContext('2d');
  if (state.chart) {
    state.chart.destroy();
  }

  state.chart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Low Risk', 'High Risk'],
      datasets: [{
        data: [safe, high],
        backgroundColor: ['#d1fae5', '#fee2e2'],
        borderColor: ['#10b981', '#ef4444'],
        borderWidth: 0,
        hoverOffset: 8
      }]
    },
    options: {
      maintainAspectRatio: false,
      responsive: true,
      cutout: '68%',
      plugins: {
        legend: { position: 'bottom' },
        tooltip: {
          callbacks: {
            label(context) {
              const value = Number(context.raw) || 0;
              return state.latestProbability
                ? `${context.label}: ${value.toFixed(1)}%`
                : `${context.label}: ${value}`;
            }
          }
        }
      }
    }
  });
}

function setResultCardState(card, isHighRisk, prediction, confidence, riskProbability) {
  card.className = `mt-4 min-h-[150px] rounded-2xl p-5 flex flex-col items-center justify-center text-center [box-shadow:0_10px_30px_rgba(0,0,0,0.08)] ${
    isHighRisk ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-700'
  }`;

  const confidenceValue = Number(confidence);
  const safeProbability = Number(riskProbability?.safe ?? (isHighRisk ? 100 - confidenceValue : confidenceValue));
  const highProbability = Number(riskProbability?.high_risk ?? (isHighRisk ? confidenceValue : 100 - confidenceValue));
  const riskState = getRiskState(prediction);

  card.innerHTML = `
    <p class="text-[12px] uppercase tracking-[0.16em] font-semibold text-slate-700">Prediction Result</p>
    <div class="mt-2 inline-flex items-center gap-2 text-[30px] font-bold leading-none">
      <span class="material-symbols-outlined text-[30px]">${riskState.icon}</span>
      ${riskState.label}
    </div>
    <p class="mt-2 text-[14px] font-semibold">Confidence: ${Number.isFinite(confidenceValue) ? confidenceValue.toFixed(1) : '-'}%</p>
    <p class="mt-1 text-[14px] font-medium text-slate-700">
      <span class="text-green-700">Low Risk: ${Number.isFinite(safeProbability) ? safeProbability.toFixed(1) : '-'}%</span>
      <span class="text-slate-400"> | </span>
      <span class="text-red-600">High Risk: ${Number.isFinite(highProbability) ? highProbability.toFixed(1) : '-'}%</span>
    </p>
  `;
}

function showLoading(card) {
  card.className = 'mt-4 min-h-[150px] rounded-2xl p-5 flex flex-col items-center justify-center text-center bg-gradient-to-br from-[#eaf1ff] to-[#f4f7ff] text-[#004ac6] [box-shadow:0_10px_30px_rgba(0,0,0,0.08)]';
  card.innerHTML = `
    <span class="material-symbols-outlined text-[28px]">hourglass_top</span>
    <p class="mt-2 text-[20px] font-bold">Awaiting Parameters</p>
    <p class="mt-1 text-[14px] text-slate-600">Analyzing route data for live risk probabilities.</p>
  `;
}

function showError(card, message) {
  card.className = 'mt-4 min-h-[150px] rounded-2xl p-5 flex flex-col items-center justify-center text-center bg-red-100 text-red-600 [box-shadow:0_10px_30px_rgba(0,0,0,0.08)]';
  card.innerHTML = `
    <p class="text-[20px] font-bold">Prediction Error</p>
    <p class="mt-1 text-[14px]">${safeText(message, 'Server error')}</p>
  `;
}

function buildModelPayload(distance, delay, weather) {
  const distanceValue = toNumber(distance, 0);
  const delayValue = toNumber(delay, 0);
  const weatherValue = toNumber(weather, 0);

  const leadTime = Math.max(1, Math.round(delayValue / 2 + distanceValue / 120));
  const shippingTimes = Math.max(1, Math.round(delayValue / 6 + distanceValue / 400));
  const defectRates = Math.min(5, Math.max(0.1, 1.2 + (weatherValue === 2 ? 1.8 : weatherValue === 1 ? 0.8 : 0) + delayValue / 20));

  return {
    distance: distanceValue,
    delay: delayValue,
    weather: weatherValue,
    Price: 50,
    Availability: 70,
    Number_of_products_sold: 400,
    Revenue_generated: 12000,
    Stock_levels: 55,
    Lead_times: leadTime,
    Shipping_times: shippingTimes,
    Shipping_carriers: 'Carrier B',
    Shipping_costs: 120 + distanceValue * 0.2,
    Location: 'Mumbai',
    Lead_time: leadTime,
    Production_volumes: 500,
    Manufacturing_lead_time: Math.max(1, Math.round(leadTime * 0.7)),
    Manufacturing_costs: 40 + distanceValue * 0.05,
    Inspection_results: weatherValue === 2 ? 'Pending' : 'Pass',
    Defect_rates: defectRates,
    Transportation_modes: distanceValue < 700 ? 'Road' : 'Rail',
    Costs: 180 + distanceValue * 0.25
  };
}

async function refreshDashboardData() {
  const historyTable = document.getElementById('historyTable');
  const riskChart = document.getElementById('riskChart');

  if (!historyTable || !riskChart) {
    return;
  }

  try {
    const historyResponse = await fetchHistoryData();
    const entries = Array.isArray(historyResponse.data) ? historyResponse.data : [];
    
    // Only render if we have entries to show
    if (entries.length > 0) {
      renderHistoryTable(entries, historyTable);
      renderRiskChart(entries, riskChart, state.latestProbability);
    } else {
      // If no backend data, just update the chart with latest probability
      if (state.latestProbability) {
        renderRiskChart([], riskChart, state.latestProbability);
      }
    }
  } catch (error) {
    // Silent failure - don't wipe the table on error
    // Just update chart if we have probability data
    if (state.latestProbability && riskChart) {
      renderRiskChart([], riskChart, state.latestProbability);
    }
  }
}

async function handlePredictSubmit(event) {
  event.preventDefault();

  const distance = document.getElementById('distance')?.value;
  const delay = document.getElementById('delay')?.value;
  const weather = document.getElementById('weather')?.value;
  const resultCard = document.getElementById('resultCard');
  const riskChart = document.getElementById('riskChart');
  const historyTable = document.getElementById('historyTable');

  if (!resultCard) {
    return;
  }

  if (distance === '' || delay === '' || weather === '') {
    showError(resultCard, 'Please fill in all fields.');
    return;
  }

  showLoading(resultCard);

  try {
    const payload = buildModelPayload(distance, delay, weather);
    const predictionResponse = await requestPrediction(payload);

    if (predictionResponse.status === 'success') {
      const isHighRisk = String(predictionResponse.prediction).includes('High');
      const riskState = getRiskState(predictionResponse.prediction);

      // Immediate UI feedback: append a local history row right after prediction.
      appendHistoryRow(
        {
          timestamp: new Date().toISOString(),
          distance: toNumber(distance, 0),
          delay: toNumber(delay, 0),
          weather: toNumber(weather, 0),
          result: riskState.label
        },
        historyTable
      );

      setResultCardState(
        resultCard,
        isHighRisk,
        predictionResponse.prediction,
        predictionResponse.confidence,
        predictionResponse.risk_probability
      );

      await refreshDashboardData();
      if (riskChart) {
        renderRiskChart([], riskChart, predictionResponse.risk_probability);
      }
    } else {
      showError(resultCard, predictionResponse.message || 'Prediction failed.');
    }
  } catch (error) {
    showError(resultCard, error?.message || 'Server error.');
  }
}

function bindEvents() {
  const predictionForm = document.getElementById('predictionForm');
  const refreshButton = document.getElementById('refreshHistoryBtn');

  predictionForm?.addEventListener('submit', handlePredictSubmit);
  refreshButton?.addEventListener('click', refreshDashboardData);
}

async function initializeDashboard() {
  bindEvents();
  const resultCard = document.getElementById('resultCard');
  if (resultCard) {
    resultCard.className = 'mt-4 min-h-[150px] rounded-2xl p-5 flex flex-col items-center justify-center text-center bg-gradient-to-br from-[#eaf1ff] to-[#f4f7ff] [box-shadow:0_10px_30px_rgba(0,0,0,0.08)]';
    resultCard.innerHTML = `
      <span class="material-symbols-outlined text-[32px] text-slate-400">autorenew</span>
      <p class="mt-3 text-[20px] font-bold">Awaiting Parameters</p>
      <p class="mt-1 text-[14px] text-slate-600">Input route data to generate a real-time risk probability matrix.</p>
    `;
  }
  await refreshDashboardData();
}

document.addEventListener('DOMContentLoaded', initializeDashboard);