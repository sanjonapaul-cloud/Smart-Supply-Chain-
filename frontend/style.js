async function predict() {
  const distance = document.getElementById("distance").value;
  const delay = document.getElementById("delay").value;
  const weather = document.getElementById("weather").value;
  const resultBox = document.getElementById("resultBox");

  if (!distance || !delay || weather === "") {
    alert("Please fill all fields");
    return;
  }

  resultBox.classList.remove("hidden");
  resultBox.innerText = "⏳ Predicting...";
  resultBox.style.background = "#e0e3e5";

  try {
    const response = await fetch("http://127.0.0.1:5000/predict", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        distance: Number(distance),
        delay: Number(delay),
        weather: Number(weather)
      })
    });

    const data = await response.json();

    if (data.status === "success") {
      resultBox.innerText = data.prediction;

      if (data.prediction.includes("High")) {
        resultBox.style.background = "#ffdad6";
        resultBox.style.color = "#93000a";
      } else {
        resultBox.style.background = "#d1fae5";
        resultBox.style.color = "#065f46";
      }

    } else {
      resultBox.innerText = data.message;
    }

  } catch (error) {
    resultBox.innerText = "❌ Server error";
  }
}


// 🔥 HISTORY FUNCTION
async function loadHistory() {
  try {
    const response = await fetch("http://127.0.0.1:5000/history");
    const data = await response.json();

    const table = document.getElementById("historyTable");
    table.innerHTML = "";

    if (data.data.length === 0) {
      table.innerHTML = `<tr><td colspan="5" class="text-center py-6">No history found</td></tr>`;
      return;
    }

    data.data.forEach(item => {
      const row = `
        <tr>
          <td class="px-8 py-6 text-sm">${item.timestamp}</td>
          <td class="px-8 py-6">${item.input.distance}</td>
          <td class="px-8 py-6">${item.input.delay}</td>
          <td class="px-8 py-6">${item.input.weather}</td>
          <td class="px-8 py-6 font-bold">${item.result}</td>
        </tr>
      `;
      table.innerHTML += row;
    });

  } catch (error) {
    console.error("History load error:", error);
  }
}


// auto load
window.onload = loadHistory;