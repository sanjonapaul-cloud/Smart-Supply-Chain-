function formatTimestamp(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString([], {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function renderHistoryTable(entries, tableElement) {
  tableElement.innerHTML = "";

  if (!entries.length) {
    tableElement.innerHTML = `
      <tr>
        <td colspan="5" class="empty-state">
          No predictions yet. Run a risk prediction to populate the ledger.
        </td>
      </tr>
    `;
    return;
  }

  function toPrimitive(value, fallback = "-") {
    if (value === null || value === undefined) {
      return fallback;
    }

    if (typeof Element !== "undefined" && value instanceof Element) {
      const elementValue = value.value;
      if (
        typeof elementValue === "string" ||
        typeof elementValue === "number" ||
        typeof elementValue === "boolean"
      ) {
        return elementValue;
      }
      return fallback;
    }

    if (typeof value === "object") {
      return fallback;
    }

    if (typeof value === "string") {
      const normalized = value.trim();
      if (!normalized || normalized === "[object HTMLInputElement]") {
        return fallback;
      }
      return normalized;
    }

    return value;
  }

  function getInputObject(item) {
    if (item && typeof item.input === "string") {
      try {
        const parsed = JSON.parse(item.input);
        if (parsed && typeof parsed === "object") {
          return parsed;
        }
      } catch {
        return {};
      }
    }

    return item?.input && typeof item.input === "object" ? item.input : {};
  }

  function getValue(source, candidates) {
    for (const key of candidates) {
      if (source && source[key] !== undefined && source[key] !== null) {
        return source[key];
      }
    }
    return undefined;
  }

  entries.forEach((item) => {
    const input = getInputObject(item);

    const rawDistance =
      getValue(input, ["distance", "Distance"]) ??
      getValue(item, ["distance", "Distance"]) ??
      "-";

    const rawDelay =
      getValue(input, ["delay", "Delay"]) ??
      getValue(item, ["delay", "Delay"]) ??
      "-";

    const rawWeather =
      getValue(input, ["weather", "Weather"]) ??
      getValue(item, ["weather", "Weather"]) ??
      0;

    const distance = toPrimitive(rawDistance, "-");
    const delay = toPrimitive(rawDelay, "-");
    const weather = toPrimitive(rawWeather, 0);

    const distanceDisplay = distance === "-" ? "-" : `${distance} km`;
    const delayDisplay = delay === "-" ? "-" : `${delay} hrs`;

    const normalizedWeather = String(weather).trim().toLowerCase();
    const weatherLabel =
      normalizedWeather === "1" || normalizedWeather === "bad" || normalizedWeather === "true"
        ? "Bad"
        : "Good";

    const isHighRisk = String(item.result).includes("High");

    const row = `
      <tr class="table-row">
        <td class="px-5 md:px-7 py-4 text-sm text-slate-600 whitespace-nowrap">
          ${formatTimestamp(item.timestamp)}
        </td>
        <td class="px-5 md:px-7 py-4 text-sm font-medium text-slate-900">
          ${distanceDisplay}
        </td>
        <td class="px-5 md:px-7 py-4 text-sm text-slate-800">
          ${delayDisplay}
        </td>
        <td class="px-5 md:px-7 py-4 text-sm text-slate-700">
          ${weatherLabel}
        </td>
        <td class="px-5 md:px-7 py-4">
          <span class="inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ${
            isHighRisk ? "bg-red-100 text-red-700" : "bg-emerald-100 text-emerald-700"
          }">
            ${item.result}
          </span>
        </td>
      </tr>
    `;

    tableElement.innerHTML += row;
  });
}
