// API client for handling data fetching
class APIClient {
  constructor() {
    this.baseURL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
  }

  async request(endpoint, options = {}) {
    try {
      const response = await fetch(`${this.baseURL}${endpoint}`, {
        headers: {
          "Content-Type": "application/json",
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      throw new Error(`API request failed: ${error.message}`);
    }
  }

  // API methods
  async getDataSources() {
    return this.request("/data-sources");
  }

  async getDataCollections() {
    return this.request("/data-collections");
  }

  async getSmartLists() {
    return this.request("/smart-lists");
  }

  async getSmartListItems(listId) {
    return this.request(`/smart-lists/${listId}/items`);
  }

  async getChats(listId) {
    return this.request(`/chats/${listId}`);
  }

  async createSmartList(listData) {
    return this.request("/smart-lists", {
      method: "POST",
      body: JSON.stringify(listData),
    });
  }

  async askQuestion(listId, question, context = []) {
    return this.request(`/chats/${listId}/ask`, {
      method: "POST",
      body: JSON.stringify({ question, context }),
    });
  }
}

export const apiClient = new APIClient();
