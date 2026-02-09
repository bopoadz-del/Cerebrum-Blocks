async function loadScenarios() {
  const response = await fetch("/api/scenarios");
  if (!response.ok) {
    throw new Error("Failed to load scenarios");
  }
  return response.json();
}

function renderScenarioSummary(data) {
  const container = document.getElementById("scenario-summary");
  if (!container) {
    return;
  }
  const defaultScenario = data.default || {};
  container.innerHTML = `
    <h3>Default Scenario</h3>
    <pre>${JSON.stringify(defaultScenario, null, 2)}</pre>
    <h3>Weibull Presets</h3>
    <pre>${JSON.stringify(data.weibull_presets, null, 2)}</pre>
  `;
}

async function init() {
  try {
    const scenarios = await loadScenarios();
    renderScenarioSummary(scenarios);
  } catch (error) {
    const container = document.getElementById("scenario-summary");
    if (container) {
      container.textContent = `Unable to load scenarios: ${error.message}`;
    }
  }
}

init();
