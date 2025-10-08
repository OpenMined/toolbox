import { defineStore } from "pinia";
import { apiClient } from "../api/client.js";

export const useDataCollectionsStore = defineStore("dataCollections", {
  state: () => ({
    collections: [],
    loading: false,
    error: null,
  }),

  getters: {
    getCollectionByDataSource: (state) => (dataSourceId) =>
      state.collections.find((collection) => collection.id === dataSourceId),

    getCollectionItems: (state) => (dataSourceId) => {
      const collection = state.collections.find((c) => c.id === dataSourceId);
      return collection ? collection.items : [];
    },

    getTotalItemCount: (state) =>
      state.collections.reduce(
        (total, collection) => total + collection.items.length,
        0,
      ),
  },

  actions: {
    async fetchCollections() {
      this.loading = true;
      this.error = null;

      try {
        this.collections = await apiClient.getDataCollections();
      } catch (error) {
        this.error = error.message;
        console.error("Failed to fetch data collections:", error);
      } finally {
        this.loading = false;
      }
    },

    async syncCollection(dataSourceId) {
      // This would trigger a sync operation on the backend
      // For now, just refetch the collections
      try {
        await this.fetchCollections();
      } catch (error) {
        console.error(`Failed to sync collection for ${dataSourceId}:`, error);
      }
    },

    // Method to add items to a collection (used by real-time updates)
    addItemsToCollection(dataSourceId, newItems) {
      const collection = this.getCollectionByDataSource(dataSourceId);
      if (collection) {
        collection.items.unshift(...newItems);
      }
    },

    // Method to update item in collection
    updateItemInCollection(dataSourceId, itemId, updates) {
      const collection = this.getCollectionByDataSource(dataSourceId);
      if (collection) {
        const itemIndex = collection.items.findIndex(
          (item) => item.id === itemId,
        );
        if (itemIndex !== -1) {
          collection.items[itemIndex] = {
            ...collection.items[itemIndex],
            ...updates,
          };
        }
      }
    },

    // Method to remove item from collection
    removeItemFromCollection(dataSourceId, itemId) {
      const collection = this.getCollectionByDataSource(dataSourceId);
      if (collection) {
        collection.items = collection.items.filter(
          (item) => item.id !== itemId,
        );
      }
    },

    // Search items across collections
    searchItems(query, dataSourceIds = null) {
      const collectionsToSearch = dataSourceIds
        ? this.collections.filter((c) => dataSourceIds.includes(c.id))
        : this.collections;

      const results = [];

      collectionsToSearch.forEach((collection) => {
        const matchingItems = collection.items.filter((item) => {
          const searchText = JSON.stringify(item.content).toLowerCase();
          return searchText.includes(query.toLowerCase());
        });
        results.push(...matchingItems);
      });

      return results;
    },
  },
});
