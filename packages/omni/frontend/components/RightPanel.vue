<template>
  <div class="h-full flex flex-col">
    <!-- Previous Questions Section -->
    <div class="p-4 border-b border-gray-200">
      <h3
        class="text-sm font-medium text-gray-900 mb-3"
        v-if="
          smartListsStore.currentList && smartListsStore.currentListDateRange
        "
      >
        Chat about {{ smartListsStore.currentList.name }} •
        {{ formatDateRange(smartListsStore.currentListDateRange) }}
      </h3>

      <!-- New Chat Button -->
      <div
        class="py-2 px-1 hover:bg-gray-50 cursor-pointer transition-colors rounded-md flex items-center space-x-2 mb-2"
        @click="handleNewChat"
      >
        <svg
          class="w-4 h-4 text-gray-500"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
          />
        </svg>
        <span class="text-sm text-gray-600">New Chat</span>
      </div>

      <!-- Chats Header -->
      <p
        v-if="chatStore.conversations.length > 0"
        class="text-xs text-gray-500 mb-2 px-1 mt-3"
      >
        Chats
      </p>

      <div class="max-h-40 overflow-y-auto space-y-1">
        <div
          v-for="conversation in chatStore.conversations"
          :key="conversation.id"
          class="py-2 px-1 hover:bg-gray-100 cursor-pointer transition-colors rounded-md"
          :class="{
            'bg-gray-100': chatStore.selectedConversationId === conversation.id,
          }"
          @click="chatStore.selectConversation(conversation.id)"
        >
          <p class="text-sm text-gray-600 truncate leading-relaxed">
            {{ conversation.question }}
          </p>
        </div>
      </div>
    </div>

    <!-- Chat Area -->
    <div class="flex-1 flex flex-col min-h-0">
      <!-- Messages -->
      <div class="flex-1 overflow-y-auto p-4 space-y-4 min-h-0">
        <!-- Empty state when no conversations exist -->
        <div
          v-if="chatStore.conversations.length === 0"
          class="text-center text-gray-500 mt-8"
        >
          <p>Ask a question about the content in your list</p>
        </div>

        <!-- Empty state when no conversation is selected (new chat mode) -->
        <div
          v-else-if="!currentConversation"
          class="flex items-center justify-center h-full"
        >
          <div class="text-center text-gray-500">
            <h2
              class="text-lg font-medium text-gray-800"
              v-if="
                smartListsStore.currentList &&
                smartListsStore.currentListDateRange
              "
            >
              Chat about {{ smartListsStore.currentList.name }} •
              {{ formatDateRange(smartListsStore.currentListDateRange) }}
            </h2>
          </div>
        </div>

        <div v-else>
          <!-- Show selected chat messages -->
          <div v-if="chatStore.selectedChat" class="space-y-4">
            <div
              v-for="message in chatStore.selectedChat.messages"
              :key="message.id"
              :class="
                message.role === 'user'
                  ? 'flex justify-end'
                  : 'flex justify-start'
              "
            >
              <div
                class="p-3 rounded-lg max-w-xs"
                :class="{
                  'bg-blue-500 text-white': message.role === 'user',
                  'bg-gray-100 text-gray-900': message.role === 'assistant',
                }"
              >
                <div
                  v-if="message.role === 'assistant'"
                  class="text-sm prose prose-sm max-w-none prose-p:my-2 prose-ul:my-2 prose-ol:my-2 prose-li:my-0"
                  v-html="renderMarkdown(message.content)"
                ></div>
                <p v-else class="text-sm">{{ message.content }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Loading indicator -->
        <div v-if="chatStore.isLoading" class="flex justify-start">
          <div class="bg-gray-100 text-gray-900 p-3 rounded-lg">
            <div class="flex items-center space-x-2">
              <div
                class="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"
              ></div>
              <p class="text-sm">Thinking...</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Input Area -->
      <div class="p-4 border-t border-gray-200">
        <div class="flex space-x-2">
          <input
            ref="chatInput"
            v-model="chatStore.currentQuestion"
            type="text"
            placeholder="Ask a question..."
            class="flex-1 p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            :disabled="chatStore.isLoading"
            @keydown.enter="handleSubmit"
          />
          <button
            class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            :disabled="!chatStore.currentQuestion.trim() || chatStore.isLoading"
            @click="handleSubmit"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { computed, ref, watch, nextTick } from "vue";
import { marked } from "marked";
import { useNewChatStore } from "../stores/newChatStore";
import { useSmartListsStore } from "../stores/smartListsStore";

export default {
  name: "RightPanel",
  setup() {
    const chatStore = useNewChatStore();
    const smartListsStore = useSmartListsStore();
    const chatInput = ref(null);

    const currentConversation = computed(() => {
      // Only show conversation if one is specifically selected
      // When selectedConversationId is null, we're in "new chat" mode
      return chatStore.selectedConversation || null;
    });

    const formatDateRange = (dateRange) => {
      if (!dateRange) return "";

      // Check if both dates are provided and valid
      if (!dateRange.from && !dateRange.to) {
        return "All time";
      }

      // If only one date is provided
      if (!dateRange.from || !dateRange.to) {
        const options = { month: "short", day: "numeric", year: "numeric" };
        if (dateRange.from) {
          const fromDate = new Date(dateRange.from);
          if (isNaN(fromDate.getTime())) return "";
          return `From ${fromDate.toLocaleDateString("en-US", options)}`;
        }
        if (dateRange.to) {
          const toDate = new Date(dateRange.to);
          if (isNaN(toDate.getTime())) return "";
          return `Until ${toDate.toLocaleDateString("en-US", options)}`;
        }
        return "";
      }

      const fromDate = new Date(dateRange.from);
      const toDate = new Date(dateRange.to);

      // Validate dates
      if (isNaN(fromDate.getTime()) || isNaN(toDate.getTime())) {
        return "";
      }

      const options = { month: "short", day: "numeric" };
      const fromFormatted = fromDate.toLocaleDateString("en-US", options);
      const toFormatted = toDate.toLocaleDateString("en-US", options);

      return `${fromFormatted} - ${toFormatted}`;
    };

    const handleSubmit = () => {
      if (chatStore.currentQuestion.trim() && !chatStore.isLoading) {
        chatStore.askQuestion(chatStore.currentQuestion);
      }
    };

    const handleNewChat = () => {
      chatStore.startNewChat();
      chatStore.focusInput();
    };

    const renderMarkdown = (content) => {
      return marked(content, {
        breaks: true,
        gfm: true,
      });
    };

    // Watch for focus input signal
    watch(
      () => chatStore.shouldFocusInput,
      (shouldFocus) => {
        if (shouldFocus && chatInput.value) {
          nextTick(() => {
            chatInput.value.focus();
            chatStore.clearFocusInput();
          });
        }
      },
    );

    return {
      chatStore,
      smartListsStore,
      chatInput,
      currentConversation,
      formatDateRange,
      handleSubmit,
      handleNewChat,
      renderMarkdown,
    };
  },
};
</script>
