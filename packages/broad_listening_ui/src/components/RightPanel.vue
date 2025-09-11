<template>
  <div class="h-full flex flex-col">
    <!-- Previous Questions Section -->
    <div class="p-4 border-b border-gray-200">
      <h3 class="text-sm font-medium text-gray-900 mb-3">Previous Questions</h3>
      <div class="max-h-40 overflow-y-auto space-y-2">
        <div
          v-for="conversation in chatStore.conversations"
          :key="conversation.id"
          class="p-2 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors"
          @click="chatStore.selectConversation(conversation.id)"
        >
          <p class="text-sm text-gray-700 truncate">
            {{ conversation.question }}
          </p>
        </div>
      </div>
    </div>

    <!-- Chat Area -->
    <div class="flex-1 flex flex-col">
      <!-- Messages -->
      <div class="flex-1 overflow-y-auto p-4 space-y-4">
        <div
          v-if="chatStore.conversations.length === 0"
          class="text-center text-gray-500 mt-8"
        >
          <p>Ask a question about the content in your list</p>
        </div>

        <div v-else>
          <!-- Show latest conversation -->
          <div v-if="latestConversation" class="space-y-4">
            <!-- User Question -->
            <div class="flex justify-end">
              <div class="bg-blue-500 text-white p-3 rounded-lg max-w-xs">
                <p class="text-sm">{{ latestConversation.question }}</p>
              </div>
            </div>

            <!-- AI Answer -->
            <div class="flex justify-start">
              <div class="bg-gray-100 text-gray-900 p-3 rounded-lg max-w-xs">
                <p class="text-sm">{{ latestConversation.answer }}</p>
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
import { computed } from "vue";
import { useChatStore } from "../stores/chatStore";

export default {
  name: "RightPanel",
  setup() {
    const chatStore = useChatStore();

    const latestConversation = computed(() => {
      return chatStore.conversations.length > 0
        ? chatStore.conversations[0]
        : null;
    });

    const handleSubmit = () => {
      if (chatStore.currentQuestion.trim() && !chatStore.isLoading) {
        chatStore.askQuestion(chatStore.currentQuestion);
      }
    };

    return {
      chatStore,
      latestConversation,
      handleSubmit,
    };
  },
};
</script>
