const BASE_URL = document.querySelector('meta[name="api-base-url"]')?.content?.trim();

if (!BASE_URL) {
	throw new Error("Missing api-base-url meta configuration");
}

async function parseJsonSafely(response, context) {
	const contentType = response.headers.get("content-type") || "";
	if (!contentType.includes("application/json")) {
		const text = await response.text();
		throw new Error(`${context} expected JSON but received: ${text.slice(0, 120)}`);
	}

	try {
		return await response.json();
	} catch (error) {
		throw new Error(`${context} returned invalid JSON`);
	}
}

export async function requestPrediction(payload) {
	const response = await fetch(`${BASE_URL}/predict`, {
		method: "POST",
		headers: {
			"Content-Type": "application/json"
		},
		body: JSON.stringify(payload)
	});

	if (!response.ok) {
		throw new Error(`Prediction request failed: ${response.status}`);
	}

	return parseJsonSafely(response, "Prediction API");
}

export async function fetchHistoryData() {
	const response = await fetch(`${BASE_URL}/history`);

	if (!response.ok) {
		throw new Error(`History request failed: ${response.status}`);
	}

	return parseJsonSafely(response, "History API");
}
