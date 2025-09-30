import { defineStore } from "pinia";
import { apiClient } from "../api/client.js";
import posthog from "posthog-js";

export const useNewChatStore = defineStore("newChat", {
  state: () => ({
    isHighlighted: false,
    currentQuestion: "",
    shouldFocusInput: false,
    isChatPanelOpen: false,
    isLoading: false,
    error: null,

    // Chat data per smart list
    chatsByList: {},
    selectedChatId: null,
    currentListId: null,
  }),

  getters: {
    currentChats: (state) => {
      if (!state.currentListId) return [];
      return state.chatsByList[state.currentListId] || [];
    },

    selectedChat: (state) => {
      if (!state.selectedChatId || !state.currentListId) return null;
      const chats = state.chatsByList[state.currentListId] || [];
      return chats.find((chat) => chat.id === state.selectedChatId);
    },

    selectedConversation: (state) => {
      // For compatibility with existing components
      const chat = state.selectedChat;
      if (!chat || !chat.messages.length) return null;

      // Convert chat format to conversation format
      const userMessage = chat.messages.find((m) => m.role === "user");
      const assistantMessage = chat.messages.find(
        (m) => m.role === "assistant",
      );

      return {
        id: chat.id,
        question: userMessage?.content || "",
        answer: assistantMessage?.content || null,
      };
    },

    // Compatibility getter for existing components
    conversations: (state) => {
      const chats = state.currentChats;
      return chats.map((chat) => {
        const userMessage = chat.messages.find((m) => m.role === "user");
        const assistantMessage = chat.messages.find(
          (m) => m.role === "assistant",
        );

        return {
          id: chat.id,
          question: userMessage?.content || "",
          answer: assistantMessage?.content || null,
        };
      });
    },

    selectedConversationId: (state) => state.selectedChatId,
  },

  actions: {
    setHighlighted(highlighted) {
      this.isHighlighted = highlighted;
    },

    setCurrentQuestion(question) {
      this.currentQuestion = question;
    },

    async fetchChats(listId) {
      if (!listId) return;

      try {
        const chats = await apiClient.getChats(listId);
        this.chatsByList[listId] = chats;
      } catch (error) {
        console.error(`Failed to fetch chats for list ${listId}:`, error);
        this.chatsByList[listId] = [];
      }
    },

    async askQuestion(question) {
      if (!question.trim() || !this.currentListId) return;

      this.isLoading = true;
      this.error = null;

      // Track question asking in PostHog
      if (typeof posthog !== "undefined" && posthog.__loaded) {
        posthog.capture("question_asked", {
          question: question,
          list_id: this.currentListId,
          is_new_chat: !this.selectedChatId,
          question_length: question.length,
          has_context: this.currentChats.length > 0,
        });
      }

      try {
        // Initialize chats array if it doesn't exist
        if (!this.chatsByList[this.currentListId]) {
          this.chatsByList[this.currentListId] = [];
        }

        let currentChat = null;

        // Check if we have a selected chat to add to
        if (this.selectedChatId) {
          currentChat = this.chatsByList[this.currentListId].find(
            (c) => c.id === this.selectedChatId,
          );
        }

        // If no selected chat or selected chat doesn't exist, create a new one
        if (!currentChat) {
          currentChat = {
            id: Date.now(),
            messages: [],
          };
          this.chatsByList[this.currentListId].unshift(currentChat);
          this.selectedChatId = currentChat.id;
        }

        // Add user message to the current chat
        const userMessage = {
          id: Date.now(),
          role: "user",
          content: question,
          timestamp: new Date().toISOString(),
        };
        currentChat.messages.push(userMessage);

        this.currentQuestion = "";

        // Get smart list items as context
        const { useSmartListsStore } = await import("./smartListsStore.js");
        const smartListsStore = useSmartListsStore();
        const listItems = smartListsStore.currentListItems || [];

        // Convert items to strings for context
        const context = listItems.map((item) =>
          typeof item === "string"
            ? item
            : item.content || JSON.stringify(item),
        );

        // Get AI response
        const response = await apiClient.askQuestion(
          this.currentListId,
          question,
          context,
        );

        // Add assistant response to the same chat
        const assistantMessage = {
          id: Date.now() + 1,
          role: "assistant",
          content:
            response.answer ||
            `Based on the current content, here's an AI-generated response to "${question}". This is a mock response that would normally be generated by analyzing the content in the selected list.`,
          timestamp: new Date().toISOString(),
        };
        currentChat.messages.push(assistantMessage);
      } catch (error) {
        this.error = error.message;
        console.error("Failed to ask question:", error);

        // Add error message to current chat
        const currentChat = this.chatsByList[this.currentListId]?.find(
          (c) => c.id === this.selectedChatId,
        );
        if (currentChat) {
          currentChat.messages.push({
            id: Date.now() + 1,
            role: "assistant",
            content:
              "Sorry, I encountered an error while processing your question. Please try again.",
            timestamp: new Date().toISOString(),
          });
        }
      } finally {
        this.isLoading = false;
      }
    },

    selectConversation(chatId) {
      this.selectedChatId = chatId;
    },

    startNewChat() {
      this.selectedChatId = null;
      this.currentQuestion = "";
    },

    focusInput() {
      this.shouldFocusInput = true;
    },

    openChatPanel() {
      this.isChatPanelOpen = true;
    },

    closeChatPanel() {
      this.isChatPanelOpen = false;
    },

    clearFocusInput() {
      this.shouldFocusInput = false;
    },

    async updateConversationsForList(listId) {
      this.currentListId = listId;

      // Fetch chats for this list if not cached
      if (!this.chatsByList[listId]) {
        await this.fetchChats(listId);
      }

      this.selectedChatId = null; // Reset to new chat when changing lists
    },

    initializeDefaultConversations() {
      // Load any default/cached conversations
      // This would be called on app initialization
    },

    // Method to delete a chat
    deleteChat(chatId) {
      if (!this.currentListId) return;

      const chats = this.chatsByList[this.currentListId];
      if (chats) {
        this.chatsByList[this.currentListId] = chats.filter(
          (chat) => chat.id !== chatId,
        );

        // If this was the selected chat, clear selection
        if (this.selectedChatId === chatId) {
          this.selectedChatId = null;
        }
      }
    },

    // Method to add a message to an existing chat
    addMessageToChat(chatId, message) {
      if (!this.currentListId) return;

      const chats = this.chatsByList[this.currentListId];
      if (chats) {
        const chat = chats.find((c) => c.id === chatId);
        if (chat) {
          chat.messages.push({
            ...message,
            id: Date.now(),
            timestamp: new Date().toISOString(),
          });
        }
      }
    },

    // Method to update a message in a chat
    updateMessageInChat(chatId, messageId, updates) {
      if (!this.currentListId) return;

      const chats = this.chatsByList[this.currentListId];
      if (chats) {
        const chat = chats.find((c) => c.id === chatId);
        if (chat) {
          const messageIndex = chat.messages.findIndex(
            (m) => m.id === messageId,
          );
          if (messageIndex !== -1) {
            chat.messages[messageIndex] = {
              ...chat.messages[messageIndex],
              ...updates,
            };
          }
        }
      }
    },
  },
});
