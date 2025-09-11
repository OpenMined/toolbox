import { defineStore } from "pinia";
import { DATA_SOURCES } from "../constants/dataSources";

export const useConnectionsStore = defineStore("connections", {
  state: () => ({
    userAccount: {
      email: "user@example.com",
    },
    showDashboard: false,
    currentDashboard: null,
    connections: [
      {
        id: 1,
        name: "Twitter",
        type: "twitter",
        isActive: true,
        icon: "twitter",
        tweetCount: 1247,
      },
      {
        id: 2,
        name: "AI Papers",
        type: "ai-papers",
        isActive: false,
        icon: "papers",
      },
      {
        id: 3,
        name: "Discord",
        type: "discord",
        isActive: false,
        icon: "discord",
        serverCount: 3,
        messageCount: 1247,
      },
    ],
    dashboardData: {
      twitter: {
        handle: "@johndoe",
        totalTweets: 1247,
        latestTweets: [
          {
            id: 1,
            content:
              "Just discovered an amazing new AI breakthrough in transformer architectures! The potential applications are endless.",
            timestamp: "2h ago",
            likes: 42,
            retweets: 18,
          },
          {
            id: 2,
            content:
              "Working on some exciting ML projects. The intersection of AI and creativity continues to amaze me every day.",
            timestamp: "5h ago",
            likes: 28,
            retweets: 7,
          },
          {
            id: 3,
            content:
              "Open source AI tools are democratizing access to advanced machine learning. This is the future!",
            timestamp: "8h ago",
            likes: 67,
            retweets: 23,
          },
        ],
        latestTweetDate: "2025-01-15",
        syftboxTweets: 342,
        embeddingCounts: {
          "ollama/nomic-embed-text": 123,
          "openai/text-embedding-3-small": 89,
        },
      },
      aiPapers: {
        totalPapers: 847,
        trendingPapers: 156,
        syftboxPapers: 23,
        latestPaper: "Jan 15",
        latestPapers: [
          {
            id: 1,
            title:
              "Attention Is All You Need: Revisiting Transformer Architectures",
            summary:
              "We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely...",
            authors: "Vaswani et al.",
            arxivId: "2401.12345",
            timestamp: "2h ago",
          },
          {
            id: 2,
            title: "Large Language Models are Few-Shot Learners",
            summary:
              "Recent work has demonstrated substantial gains on many NLP tasks and benchmarks by pre-training on a large corpus of text followed by fine-tuning...",
            authors: "Brown et al.",
            arxivId: "2401.12346",
            timestamp: "5h ago",
          },
          {
            id: 3,
            title: "Constitutional AI: Harmlessness from AI Feedback",
            summary:
              "As AI systems become more capable, we would like to enlist their help to supervise other AIs. We experiment with methods for training a harmless AI assistant...",
            authors: "Bai et al.",
            arxivId: "2401.12347",
            timestamp: "8h ago",
          },
        ],
        embeddingCounts: {
          "ollama/nomic-embed-text": 234,
          "openai/text-embedding-3-small": 178,
        },
      },
      discord: {
        totalServers: 3,
        totalChannels: 8,
        totalMessages: 1247,
        latestActivity: "Jan 15",
        embeddingCounts: {
          "ollama/nomic-embed-text": 156,
          "openai/text-embedding-3-small": 98,
        },
      },
    },
  }),

  actions: {
    addConnection(connection) {
      this.connections.push({
        ...connection,
        id: Date.now(),
      });
    },

    toggleConnection(id) {
      const connection = this.connections.find((c) => c.id === id);
      if (connection) {
        // First, deactivate all connections and close any dashboard
        this.connections.forEach((c) => (c.isActive = false));

        // Then activate the selected connection and show its dashboard
        connection.isActive = true;
        this.showDashboard = true;

        if (connection.type === "twitter") {
          this.currentDashboard = "TwitterDashboard";
        } else if (connection.type === "ai-papers") {
          this.currentDashboard = "AIPapersDashboard";
        } else if (connection.type === "discord") {
          this.currentDashboard = "DiscordDashboard";
        }
      }
    },

    setDashboardView(dashboardComponent) {
      this.showDashboard = true;
      this.currentDashboard = dashboardComponent;
    },

    closeDashboard() {
      this.showDashboard = false;
      this.currentDashboard = null;
      // Deactivate all connections when closing dashboard
      this.connections.forEach((c) => (c.isActive = false));
    },

    showAddConnector() {
      this.setDashboardView("ConnectorManager");
    },

    getDataSources() {
      return DATA_SOURCES;
    },
  },
});
