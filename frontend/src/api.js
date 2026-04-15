const API_BASE = "https://cerebrum-platform-api.onrender.com";
const API_KEY = "cb_dev_key";

export const apiCall = async (endpoint, body) => {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${API_KEY}`
    },
    body: JSON.stringify(body)
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`HTTP ${response.status}: ${errorText}`);
  }

  return response.json();
};
