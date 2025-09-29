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

  async getSmartLists(userEmail = "dev@example.com") {
    return this.request(`/smart-lists?user_email=${userEmail}`);
  }

  async getFollowedSmartLists(userEmail = "dev@example.com") {
    return this.request(`/smart-lists/followed?user_email=${userEmail}`);
  }

  async getNotFollowingSmartLists(userEmail = "dev@example.com") {
    return this.request(`/smart-lists/not_following?user_email=${userEmail}`);
  }

  async followSmartList(listId, userEmail = "dev@example.com") {
    return this.request(
      `/smart-lists/${listId}/follow?user_email=${userEmail}`,
      {
        method: "POST",
      },
    );
  }

  async unfollowSmartList(listId, userEmail = "dev@example.com") {
    return this.request(
      `/smart-lists/${listId}/follow?user_email=${userEmail}`,
      {
        method: "DELETE",
      },
    );
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

  async registerUser(userData) {
    return this.request("/users/register", {
      method: "POST",
      body: JSON.stringify(userData),
    });
  }

  async getUser(email) {
    return this.request(`/users/${email}`);
  }

  async getMySmartLists(userEmail = "dev@example.com") {
    return this.request(`/smart-lists/my?user_email=${userEmail}`);
  }

  async getCommunitySmartLists(userEmail = "dev@example.com") {
    return this.request(`/smart-lists/community?user_email=${userEmail}`);
  }

  async deleteSmartList(listId, userEmail = "dev@example.com") {
    return this.request(`/smart-lists/${listId}?user_email=${userEmail}`, {
      method: "DELETE",
    });
  }

  async checkTwitterAccount(handle) {
    return this.request("/twitter/check-account", {
      method: "POST",
      body: JSON.stringify({ handle }),
    });
  }

  async getTweetCounts(handles) {
    return this.request("/twitter/tweet-counts", {
      method: "POST",
      body: JSON.stringify({ handles }),
    });
  }
}

export const apiClient = new APIClient();
