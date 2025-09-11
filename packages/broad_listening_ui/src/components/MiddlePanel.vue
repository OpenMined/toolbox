<template>
  <div class="h-full flex flex-col">
    <!-- Top Bar -->
    <div
      class="flex items-center justify-between p-4 border-b border-gray-200 bg-white"
    >
      <h2 class="text-lg font-semibold text-gray-900">
        {{ listsStore.currentList?.name || "Select a List" }}
      </h2>

      <div class="flex space-x-1 bg-gray-100 rounded-lg p-1">
        <button
          v-for="view in views"
          :key="view.id"
          class="px-3 py-1 text-sm font-medium rounded-md transition-colors"
          :class="getViewButtonClass(view)"
          :disabled="view.disabled"
          @click="handleViewChange(view)"
        >
          {{ view.label }}
        </button>
      </div>
    </div>

    <!-- Content Area -->
    <div class="flex-1 overflow-hidden">
      <!-- Feed View -->
      <div
        v-if="listsStore.currentView === 'feed'"
        class="h-full overflow-y-auto"
      >
        <FeedView />
      </div>

      <!-- Summary View -->
      <div v-else-if="listsStore.currentView === 'summary'" class="h-full p-6">
        <SummaryView />
      </div>

      <!-- Timeline View (Disabled) -->
      <div
        v-else-if="listsStore.currentView === 'timeline'"
        class="h-full flex items-center justify-center"
      >
        <p class="text-gray-500">Timeline view is currently disabled</p>
      </div>

      <!-- Ask View -->
      <div
        v-else-if="listsStore.currentView === 'ask'"
        class="h-full flex items-center justify-center"
      >
        <p class="text-gray-500">Ask questions in the right panel</p>
      </div>
    </div>
  </div>
</template>

<script>
import { useListsStore } from "../stores/listsStore";
import { useChatStore } from "../stores/chatStore";
import FeedView from "./FeedView.vue";
import SummaryView from "./SummaryView.vue";

export default {
  name: "MiddlePanel",
  components: {
    FeedView,
    SummaryView,
  },
  setup() {
    const listsStore = useListsStore();
    const chatStore = useChatStore();

    const views = [
      { id: "feed", label: "Feed", disabled: false },
      { id: "summary", label: "Summary", disabled: false },
      { id: "timeline", label: "Timeline", disabled: true },
      { id: "ask", label: "Ask", disabled: false },
    ];

    const getViewButtonClass = (view) => {
      const baseClass =
        "px-3 py-1 text-sm font-medium rounded-md transition-colors";
      if (view.disabled) {
        return `${baseClass} text-gray-400 cursor-not-allowed`;
      }
      if (view.id === listsStore.currentView) {
        return `${baseClass} bg-white text-gray-900 shadow-sm`;
      }
      return `${baseClass} text-gray-600 hover:text-gray-900`;
    };

    const handleViewChange = (view) => {
      if (view.disabled) return;

      if (view.id === "ask") {
        chatStore.setHighlighted(true);
        // Reset highlight after 2 seconds
        setTimeout(() => {
          chatStore.setHighlighted(false);
        }, 2000);
      }

      listsStore.setCurrentView(view.id);
    };

    return {
      listsStore,
      chatStore,
      views,
      getViewButtonClass,
      handleViewChange,
    };
  },
};
</script>
