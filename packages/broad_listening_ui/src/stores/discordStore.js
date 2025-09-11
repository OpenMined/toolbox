import { defineStore } from "pinia";

export const useDiscordStore = defineStore("discord", {
  state: () => ({
    servers: [
      {
        id: 1,
        name: "AI Development Hub",
        members: 2847,
      },
      {
        id: 2,
        name: "Machine Learning Research",
        members: 1523,
      },
      {
        id: 3,
        name: "Open Source Contributors",
        members: 934,
      },
    ],
    channels: [
      { id: 1, serverId: 1, name: "general", messageCount: 1247 },
      { id: 2, serverId: 1, name: "ai-discussion", messageCount: 892 },
      { id: 3, serverId: 1, name: "model-releases", messageCount: 634 },
      { id: 4, serverId: 1, name: "paper-reviews", messageCount: 423 },
      { id: 5, serverId: 2, name: "research-updates", messageCount: 356 },
      { id: 6, serverId: 2, name: "code-sharing", messageCount: 289 },
      { id: 7, serverId: 3, name: "project-showcase", messageCount: 167 },
      { id: 8, serverId: 3, name: "help-wanted", messageCount: 134 },
    ],
    messages: [
      {
        id: 1,
        channelId: 1,
        serverId: 1,
        username: "AIResearcher_42",
        content:
          "Just published a new paper on transformer architecture improvements. The attention mechanism we developed shows 15% better performance on long sequences!",
        avatar: "https://i.pravatar.cc/128?u=airesearcher42",
        timestamp: "2h ago",
        date: "2024-12-28",
      },
      {
        id: 2,
        channelId: 1,
        serverId: 1,
        username: "CodeMaster_Dev",
        content:
          "Amazing work! Have you considered open-sourcing the implementation? The community would love to experiment with it.",
        avatar: "https://i.pravatar.cc/128?u=codemaster",
        timestamp: "2h ago",
        date: "2024-12-28",
      },
      {
        id: 3,
        channelId: 2,
        serverId: 1,
        username: "DataScienceGuru",
        content:
          "OpenAI's latest GPT-5 preview is incredible. The multimodal capabilities are game-changing for my computer vision projects.",
        avatar: "https://i.pravatar.cc/128?u=datascienceguru",
        timestamp: "4h ago",
        date: "2024-12-28",
      },
      {
        id: 4,
        channelId: 2,
        serverId: 1,
        username: "MLEngineer_Pro",
        content:
          "I've been testing it on document analysis tasks. The accuracy improvement over GPT-4 is remarkable - especially for technical documents.",
        avatar: "https://i.pravatar.cc/128?u=mlengineer",
        timestamp: "3h ago",
        date: "2024-12-28",
      },
      {
        id: 5,
        channelId: 3,
        serverId: 1,
        username: "ModelTrainer_AI",
        content:
          "Claude 3.5 Sonnet just got updated with better coding capabilities. Anyone else notice the improvement in code generation quality?",
        avatar: "https://i.pravatar.cc/128?u=modeltrainer",
        timestamp: "6h ago",
        date: "2024-12-27",
      },
      {
        id: 6,
        channelId: 3,
        serverId: 1,
        username: "NeuralNet_Ninja",
        content:
          "Yes! The Python code it generates now follows better practices and includes more comprehensive error handling.",
        avatar: "https://i.pravatar.cc/128?u=neuralnet",
        timestamp: "5h ago",
        date: "2024-12-27",
      },
      {
        id: 7,
        channelId: 4,
        serverId: 1,
        username: "PaperReviewer_PhD",
        content:
          "Just finished reviewing the latest DeepMind paper on AlphaCode 3. The results on competitive programming are unprecedented.",
        avatar: "https://i.pravatar.cc/128?u=paperreviewer",
        timestamp: "8h ago",
        date: "2024-12-27",
      },
      {
        id: 8,
        channelId: 5,
        serverId: 2,
        username: "ResearchLead_ML",
        content:
          "Our team published new findings on few-shot learning. The methodology could revolutionize how we approach domain adaptation.",
        avatar: "https://i.pravatar.cc/128?u=researchlead",
        timestamp: "10h ago",
        date: "2024-12-27",
      },
      {
        id: 9,
        channelId: 6,
        serverId: 2,
        username: "OpenSource_Hero",
        content:
          "Sharing my latest RAG implementation using ChromaDB and LangChain. Achieved 94% accuracy on complex queries!",
        avatar: "https://i.pravatar.cc/128?u=opensource",
        timestamp: "12h ago",
        date: "2024-12-27",
      },
      {
        id: 10,
        channelId: 7,
        serverId: 3,
        username: "ProjectBuilder_99",
        content:
          "Built an AI-powered code review tool that integrates with GitHub. It catches bugs that traditional linters miss!",
        avatar: "https://i.pravatar.cc/128?u=projectbuilder",
        timestamp: "1d ago",
        date: "2024-12-26",
      },
    ],
  }),

  getters: {
    getMessagesByChannel: (state) => (channelId) => {
      return state.messages.filter(
        (message) => message.channelId === channelId,
      );
    },
    getChannelsByServer: (state) => (serverId) => {
      return state.channels.filter((channel) => channel.serverId === serverId);
    },
  },

  actions: {
    addMessage(message) {
      this.messages.unshift({
        id: Date.now(),
        timestamp: "now",
        date: new Date().toISOString().split("T")[0],
        ...message,
      });
    },
  },
});
