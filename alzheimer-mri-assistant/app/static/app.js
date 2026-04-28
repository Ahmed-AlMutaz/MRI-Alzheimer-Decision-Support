const form = document.getElementById("predictForm");
const fileInput = document.getElementById("fileInput");
const submitBtn = document.getElementById("submitBtn");
const statusEl = document.getElementById("status");
const resultEl = document.getElementById("result");

const labelEl = document.getElementById("label");
const confidenceEl = document.getElementById("confidence");
const explanationEl = document.getElementById("explanation");
const probsEl = document.getElementById("probs");
const disclaimerEl = document.getElementById("disclaimer");

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (!fileInput.files || fileInput.files.length === 0) {
    statusEl.textContent = "Please select an image first.";
    return;
  }

  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append("file", file);

  submitBtn.disabled = true;
  statusEl.textContent = "Analyzing MRI...";
  resultEl.classList.add("hidden");

  try {
    const response = await fetch("/api/predict", {
      method: "POST",
      body: formData,
    });

    const payload = await response.json();

    if (!response.ok) {
      throw new Error(payload.detail || "Prediction failed.");
    }

    labelEl.textContent = payload.label;
    confidenceEl.textContent = `${(payload.confidence * 100).toFixed(2)}%`;
    explanationEl.textContent = payload.explanation;
    disclaimerEl.textContent = payload.disclaimer;

    probsEl.innerHTML = "";
    Object.entries(payload.probabilities).forEach(([name, value]) => {
      const li = document.createElement("li");
      li.textContent = `${name}: ${(value * 100).toFixed(2)}%`;
      probsEl.appendChild(li);
    });

    statusEl.textContent = "Analysis completed.";
    resultEl.classList.remove("hidden");
  } catch (error) {
    statusEl.textContent = error.message;
  } finally {
    submitBtn.disabled = false;
  }
});
