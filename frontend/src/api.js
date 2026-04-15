const API_BASE = "https://cerebrum-platform-api.onrender.com";
const API_KEY = "cb_dev_key";

class UniversalAPI {
  constructor() {
    this.base = API_BASE;
    this.key = API_KEY;
  }

  async call(endpoint, body = {}) {
    try {
      const response = await fetch(`${this.base}${endpoint}`, {
        method: "POST",
        mode: "cors",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${this.key}`
        },
        body: JSON.stringify(body)
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      return await response.json();
    } catch (error) {
      console.error("API call failed:", error);
      throw error;
    }
  }

  async del(endpoint) {
    try {
      const response = await fetch(`${this.base}${endpoint}`, {
        method: "DELETE",
        mode: "cors",
        headers: {
          "Authorization": `Bearer ${this.key}`
        }
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      return response;
    } catch (error) {
      console.error("API delete failed:", error);
      throw error;
    }
  }

  raw(endpoint, body = {}) {
    return fetch(`${this.base}${endpoint}`, {
      method: "POST",
      mode: "cors",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${this.key}`
      },
      body: JSON.stringify(body)
    });
  }

  // Convenience methods
  chat(message) {
    return this.call("/v1/chat", { message });
  }

  chain(data) {
    return this.call("/v1/chain", data);
  }

  execute(block, params) {
    return this.call("/v1/execute", { block, params });
  }

  upload(fileData) {
    return this.call("/v1/upload", fileData);
  }
}

// Export singleton
export const API = new UniversalAPI();
export default API;
