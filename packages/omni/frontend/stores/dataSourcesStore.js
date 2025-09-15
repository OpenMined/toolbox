import { defineStore } from "pinia";
import { apiClient } from "../api/client.js";

export const useDataSourcesStore = defineStore("dataSources", {
  state: () => ({
    dataSources: [],
    loading: false,
    error: null,
    showDashboard: false,
    currentDashboard: null,
  }),

  getters: {
    connectedDataSources: (state) =>
      state.dataSources.filter((ds) => ds.connectionState === "connected"),

    getDataSourceById: (state) => (id) =>
      state.dataSources.find((ds) => ds.id === id),

    hasActiveConnections: (state) =>
      state.dataSources.some((ds) => ds.connectionState === "connected"),
  },

  actions: {
    async fetchDataSources() {
      this.loading = true;
      this.error = null;

      try {
        this.dataSources = await apiClient.getDataSources();
      } catch (error) {
        this.error = error.message;
        console.error("Failed to fetch data sources:", error);
      } finally {
        this.loading = false;
      }
    },

    async toggleConnection(dataSourceId) {
      const dataSource = this.getDataSourceById(dataSourceId);
      if (!dataSource) return;

      // First, deactivate all connections and close any dashboard
      this.dataSources.forEach((ds) => {
        if (ds.id !== dataSourceId) {
          // For now, we don't change connection state, just dashboard view
        }
      });

      // Toggle dashboard view for this data source
      if (this.currentDashboard === `${dataSourceId}Dashboard`) {
        this.closeDashboard();
      } else {
        this.showDashboard = true;
        this.currentDashboard = this.getDashboardComponent(dataSourceId);
      }
    },

    getDashboardComponent(dataSourceId) {
      const componentMap = {
        twitter: "TwitterDashboard",
        "ai-papers": "AIPapersDashboard",
        discord: "DiscordDashboard",
      };
      return componentMap[dataSourceId] || null;
    },

    setDashboardView(dashboardComponent) {
      this.showDashboard = true;
      this.currentDashboard = dashboardComponent;
    },

    closeDashboard() {
      this.showDashboard = false;
      this.currentDashboard = null;
    },

    showAddConnector() {
      this.setDashboardView("ConnectorManager");
    },

    // Method to update connection state (would be called after real API operations)
    updateConnectionState(dataSourceId, newState) {
      const dataSource = this.getDataSourceById(dataSourceId);
      if (dataSource) {
        dataSource.connectionState = newState;
      }
    },

    // Method to update dashboard data
    updateDashboardData(dataSourceId, newData) {
      const dataSource = this.getDataSourceById(dataSourceId);
      if (dataSource) {
        dataSource.dashboardData = { ...dataSource.dashboardData, ...newData };
      }
    },
  },
});
