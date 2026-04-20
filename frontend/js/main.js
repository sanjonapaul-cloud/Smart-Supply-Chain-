import { requestPrediction, fetchHistoryData } from "./api.js";
import { renderHistoryTable } from "./history.js";
import { renderRiskChart } from "./chart.js";
import {
  showPredictionLoading,
  showPredictionResult,
  showPredictionError
} from "./ui.js";

async function loadComponent(slotSelector, componentPath) {
  const slot = document.querySelector(slotSelector);
  if (!slot) {
    return;
  }

  const response = await fetch(componentPath);
  const markup = await response.text();
  slot.innerHTML = markup;
}

async function refreshDashboardData() {
  const historyTable = document.getElementById("historyTable");
  const riskChart = document.getElementById("riskChart");

  if (!historyTable || !riskChart) {
    return;
  }

  try {
    const historyResponse = await fetchHistoryData();
    const entries = Array.isArray(historyResponse.data) ? historyResponse.data : [];

    renderHistoryTable(entries, historyTable);
    renderRiskChart(entries, riskChart);
  } catch (error) {
    historyTable.innerHTML = `
      <tr>
        <td colspan="5" class="empty-state">Unable to load history right now.</td>
      </tr>
    `;
  }
}

async function handlePredictSubmit(event) {
  event.preventDefault();

  const distance = document.getElementById("distance")?.value;
  const delay = document.getElementById("delay")?.value;
  const weather = document.getElementById("weather")?.value;
  const resultBox = document.getElementById("resultBox");

  if (!resultBox) {
    return;
  }

  if (!distance || !delay || weather === "") {
    alert("Please fill all fields");
    return;
  }

  showPredictionLoading(resultBox);

  try {
    const distanceValue = Number(distance);
    const delayValue = Number(delay);
    const weatherValue = Number(weather);

    // Keep the simple UI inputs, but construct the full feature payload
    // required by the trained backend model.
    const leadTime = Math.max(1, Math.round(delayValue / 2 + distanceValue / 120));
    const shippingTimes = Math.max(1, Math.round(delayValue / 6 + distanceValue / 400));
    const defectRates = Math.min(5, Math.max(0.1, 1.2 + (weatherValue === 1 ? 1.8 : 0) + delayValue / 20));

    const predictionResponse = await requestPrediction({
      // legacy fields for history rendering in the current UI
      distance: distanceValue,
      delay: delayValue,
      weather: weatherValue,

      // full model feature set
      Price: 50.0,
      Availability: 70,
      Number_of_products_sold: 400,
      Revenue_generated: 12000.0,
      Stock_levels: 55,
      Lead_times: leadTime,
      Shipping_times: shippingTimes,
      Shipping_carriers: "Carrier B",
      Shipping_costs: 120.0 + distanceValue * 0.2,
      Location: "Mumbai",
      Lead_time: leadTime,
      Production_volumes: 500,
      Manufacturing_lead_time: Math.max(1, Math.round(leadTime * 0.7)),
      Manufacturing_costs: 40.0 + distanceValue * 0.05,
      Inspection_results: weatherValue === 1 ? "Pending" : "Pass",
      Defect_rates: defectRates,
      Transportation_modes: distanceValue < 700 ? "Road" : "Rail",
      Costs: 180.0 + distanceValue * 0.25
    });

    if (predictionResponse.status === "success") {
      showPredictionResult(resultBox, predictionResponse.prediction);
      await refreshDashboardData();
    } else {
      showPredictionError(resultBox, predictionResponse.message || "Prediction failed");
    }
  } catch (error) {
    showPredictionError(resultBox, "Server error");
  }
}

function bindUIEvents() {
  const predictionForm = document.getElementById("predictionForm");
  const refreshButton = document.getElementById("refreshHistoryBtn");

  if (predictionForm) {
    predictionForm.addEventListener("submit", handlePredictSubmit);
  }

  if (refreshButton) {
    refreshButton.addEventListener("click", refreshDashboardData);
  }
}

async function initializeDashboard() {
  await Promise.all([
    loadComponent("#sidebar-slot", "components/sidebar.html"),
    loadComponent("#navbar-slot", "components/navbar.html"),
    loadComponent("#cards-slot", "components/cards.html")
  ]);

  bindUIEvents();
  await refreshDashboardData();
}

document.addEventListener("DOMContentLoaded", initializeDashboard);
