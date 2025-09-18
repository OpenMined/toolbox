import { defineStore } from "pinia";
import { apiClient } from "../api/client.js";

export const useSmartListsStore = defineStore("smartLists", {
  state: () => ({
    smartLists: [],
    currentListId: null,
    currentView: "feed",
    loading: false,
    error: null,

    // Cache for computed items per list
    computedItemsCache: {},

    // Cache for list summaries
    summariesCache: {},
  }),

  getters: {
    currentList: (state) =>
      state.smartLists.find((list) => list.id === state.currentListId),

    currentListItems: (state) => {
      if (!state.currentListId) return [];
      return state.computedItemsCache[state.currentListId] || [];
    },

    currentListSummary: (state) => {
      if (!state.currentListId) return null;
      return state.summariesCache[state.currentListId] || null;
    },

    currentListDateRange: (state) => {
      const currentList = state.smartLists.find(
        (list) => list.id === state.currentListId,
      );
      if (!currentList || !currentList.listSources.length) return null;

      // Get date range from first data source (for now)
      return currentList.listSources[0].filters.dateRange;
    },

    getListById: (state) => (id) =>
      state.smartLists.find((list) => list.id === id),
  },

  actions: {
    async fetchSmartLists() {
      this.loading = true;
      this.error = null;

      try {
        this.smartLists = await apiClient.getSmartLists();
      } catch (error) {
        this.error = error.message;
        console.error("Failed to fetch smart lists:", error);
      } finally {
        this.loading = false;
      }
    },

    async fetchListItems(listId) {
      if (!listId) return;

      try {
        const items = await apiClient.getSmartListItems(listId);
        this.computedItemsCache[listId] = items;
      } catch (error) {
        console.error(`Failed to fetch items for list ${listId}:`, error);
        this.computedItemsCache[listId] = [];
      }
    },

    async setCurrentList(listId) {
      this.currentListId = listId;

      // Fetch items for this list if not cached
      if (!this.computedItemsCache[listId]) {
        await this.fetchListItems(listId);
      }

      // Update chat store when list changes
      const { useNewChatStore } = await import("./newChatStore.js");
      const chatStore = useNewChatStore();
      chatStore.updateConversationsForList(listId);
    },

    setCurrentView(view) {
      this.currentView = view;
    },

    async createSmartList(listData) {
      try {
        const newList = await apiClient.createSmartList(listData);
        this.smartLists.push(newList);

        // Initialize empty cache for the new list
        this.computedItemsCache[newList.id] = [];
        this.summariesCache[newList.id] = null;

        return newList.id;
      } catch (error) {
        console.error("Failed to create smart list:", error);
        throw error;
      }
    },

    async updateSmartList(listId, updates) {
      try {
        // Update local state immediately
        const listIndex = this.smartLists.findIndex(
          (list) => list.id === listId,
        );
        if (listIndex !== -1) {
          this.smartLists[listIndex] = {
            ...this.smartLists[listIndex],
            ...updates,
          };
        }

        // Clear cached items since filters might have changed
        delete this.computedItemsCache[listId];
        delete this.summariesCache[listId];

        // Re-fetch items with new filters
        await this.fetchListItems(listId);

        // In a real implementation, this would make an API call
        // await apiClient.updateSmartList(listId, updates);
      } catch (error) {
        console.error("Failed to update smart list:", error);
        throw error;
      }
    },

    async deleteSmartList(listId) {
      try {
        // Remove from local state
        this.smartLists = this.smartLists.filter((list) => list.id !== listId);

        // Clear cache
        delete this.computedItemsCache[listId];
        delete this.summariesCache[listId];

        // If this was the current list, clear selection
        if (this.currentListId === listId) {
          this.currentListId = null;
        }

        // In a real implementation, this would make an API call
        // await apiClient.deleteSmartList(listId);
      } catch (error) {
        console.error("Failed to delete smart list:", error);
        throw error;
      }
    },

    async generateSummary(listId, forceRefresh = false) {
      if (!listId) return { summary: null, status: "error" };

      try {
        // Check if we already have a cached completed summary (unless forced refresh)
        const cached = this.summariesCache[listId];
        if (!forceRefresh && cached && cached.status === "completed") {
          return cached;
        }

        // Fetch summary from API
        const result = await apiClient.request(
          `/smart-lists/${listId}/summary`,
        );

        // Handle both old string format and new object format
        const summaryData =
          typeof result === "string"
            ? { summary: result, status: "completed" }
            : result;

        // Cache the result
        this.summariesCache[listId] = summaryData;
        return summaryData;
      } catch (error) {
        console.error(`Failed to generate summary for list ${listId}:`, error);
        return { summary: null, status: "error" };
      }
    },

    async pollSummaryStatus(listId, onUpdate) {
      if (!listId) return;

      const maxPolls = 30; // Max 30 polls (5 minutes with 10s intervals)
      let pollCount = 0;

      const poll = async () => {
        if (pollCount >= maxPolls) {
          console.warn(`Summary generation timeout for list ${listId}`);
          return;
        }

        try {
          // Force refresh to get latest status from server
          const result = await this.generateSummary(listId, true);

          // Call the update callback
          if (onUpdate) {
            onUpdate(result);
          }

          // Continue polling if still generating
          if (result.status === "generating") {
            pollCount++;
            setTimeout(poll, 5000); // Poll every 5 seconds
          }
        } catch (error) {
          console.error("Error polling summary status:", error);
          if (onUpdate) {
            onUpdate({ summary: null, status: "error" });
          }
        }
      };

      // Start polling
      poll();
    },

    // Method to refresh computed items (trigger backend recomputation)
    async refreshComputedItems(listId) {
      if (!listId) return;

      try {
        // Clear cache first
        delete this.computedItemsCache[listId];

        // Fetch fresh items
        await this.fetchListItems(listId);
      } catch (error) {
        console.error(`Failed to refresh items for list ${listId}:`, error);
      }
    },

    // Method to add a new data source to a smart list
    addDataSourceToList(listId, dataSourceConfig) {
      const list = this.getListById(listId);
      if (list) {
        list.listSources.push(dataSourceConfig);

        // Clear cached items since we added a new data source
        delete this.computedItemsCache[listId];

        // Refresh items
        this.refreshComputedItems(listId);
      }
    },

    // Method to remove a data source from a smart list
    removeDataSourceFromList(listId, dataSourceId) {
      const list = this.getListById(listId);
      if (list) {
        list.listSources = list.listSources.filter(
          (source) => source.dataSourceId !== dataSourceId,
        );

        // Clear cached items since we removed a data source
        delete this.computedItemsCache[listId];

        // Refresh items
        this.refreshComputedItems(listId);
      }
    },

    // Method to update filters for a data source in a smart list
    updateDataSourceFilters(listId, dataSourceId, newFilters) {
      const list = this.getListById(listId);
      if (list) {
        const sourceConfig = list.listSources.find(
          (source) => source.dataSourceId === dataSourceId,
        );
        if (sourceConfig) {
          sourceConfig.filters = { ...sourceConfig.filters, ...newFilters };

          // Clear cached items since filters changed
          delete this.computedItemsCache[listId];

          // Refresh items
          this.refreshComputedItems(listId);
        }
      }
    },
  },
});
