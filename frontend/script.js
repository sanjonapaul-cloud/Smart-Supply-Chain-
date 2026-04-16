async function predict() {
  const distance = document.getElementById("distance").value;
  const delay = document.getElementById("delay").value;
  const weather = document.getElementById("weather").value;
  const resultDiv = document.getElementById("result");

  if (!distance || !delay || weather === "") {
    resultDiv.innerText = "⚠ Please fill all fields";
    resultDiv.style.color = "orange";
    return;
  }

  resultDiv.innerText = "⏳ Predicting...";
  resultDiv.style.color = "black";

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
      resultDiv.innerText = data.prediction;

      // color based on result
      if (data.prediction.includes("High")) {
        resultDiv.style.color = "red";
      } else {
        resultDiv.style.color = "green";
      }

    } else {
      resultDiv.innerText = data.message;
      resultDiv.style.color = "red";
    }

  } catch (error) {
    resultDiv.innerText = "❌ Server error";
    resultDiv.style.color = "red";
  }
}