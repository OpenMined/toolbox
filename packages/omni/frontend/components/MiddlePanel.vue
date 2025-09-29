<template>
  <div class="h-full flex flex-col">
    <!-- Top Bar -->
    <div class="border-b border-gray-200 bg-white">
      <!-- Main header row -->
      <div class="flex items-center justify-between p-4">
        <div class="flex-1 min-w-0">
          <h2 class="text-lg font-semibold text-gray-900 truncate">
            {{ smartListsStore.currentList?.name || "Select a List" }}
          </h2>
        </div>

        <div class="flex space-x-1 bg-gray-100 rounded-lg p-1 ml-4">
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

      <!-- Authors row -->
      <div
        v-if="smartListsStore.currentList && currentListAuthors.length > 0"
        class="px-4 pb-4"
      >
        <div class="flex items-center flex-wrap gap-2">
          <!-- Always visible authors -->
          <template v-for="(author, index) in displayedAuthors" :key="author">
            <div
              class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 hover:bg-blue-200 transition-colors"
            >
              <span class="text-blue-600 mr-1">@</span>{{ author }}
              <!-- Loading indicator for authors with 0 tweets -->
              <div
                v-if="isAuthorLoading(author)"
                class="ml-1.5 animate-spin h-3 w-3"
                title="Loading tweets..."
              >
                <svg
                  class="w-3 h-3 text-blue-600"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    class="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    stroke-width="4"
                  ></circle>
                  <path
                    class="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
              </div>
              <!-- Twitter link for Twitter sources -->
              <button
                v-else-if="isTwitterSource"
                @click="openTwitterProfile(author)"
                class="ml-1.5 text-blue-600 hover:text-blue-800 transition-colors"
                title="View Twitter profile"
              >
                <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z"
                  />
                  <path
                    d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-1a1 1 0 10-2 0v1H5V7h1a1 1 0 000-2H5z"
                  />
                </svg>
              </button>
            </div>
          </template>

          <!-- Show more/less toggle -->
          <button
            v-if="currentListAuthors.length > 5"
            @click="toggleAuthorsExpanded"
            class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600 hover:bg-gray-200 transition-colors"
          >
            <span v-if="authorsExpanded">
              Show less
              <svg class="w-3 h-3 ml-1" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fill-rule="evenodd"
                  d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z"
                  clip-rule="evenodd"
                />
              </svg>
            </span>
            <span v-else>
              +{{ currentListAuthors.length - 5 }} more
              <svg class="w-3 h-3 ml-1" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fill-rule="evenodd"
                  d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                  clip-rule="evenodd"
                />
              </svg>
            </span>
          </button>
        </div>
      </div>
    </div>

    <!-- Content Area -->
    <div class="flex-1 overflow-hidden">
      <!-- Feed View -->
      <div
        v-if="smartListsStore.currentView === 'feed'"
        class="h-full overflow-y-auto"
      >
        <FeedView />
      </div>

      <!-- Timeline View (Disabled) -->
      <div
        v-else-if="smartListsStore.currentView === 'timeline'"
        class="h-full flex items-center justify-center"
      >
        <p class="text-gray-500">Timeline view is currently disabled</p>
      </div>

      <!-- Ask View -->
      <div
        v-else-if="smartListsStore.currentView === 'ask'"
        class="h-full flex items-center justify-center"
      >
        <p class="text-gray-500">Ask questions in the right panel</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onUnmounted } from "vue";
import { useSmartListsStore } from "../stores/smartListsStore";
import { useNewChatStore } from "../stores/newChatStore";
import { apiClient } from "../api/client";
import FeedView from "./FeedView.vue";

export default {
  name: "MiddlePanel",
  components: {
    FeedView,
  },
  setup() {
    const smartListsStore = useSmartListsStore();
    const chatStore = useNewChatStore();
    const authorsExpanded = ref(false);
    const authorTweetCounts = ref({});
    const pollingInterval = ref(null);

    const views = [
      { id: "feed", label: "Smart Feed", disabled: false },
      { id: "timeline", label: "Timeline", disabled: true },
      { id: "ask", label: "Ask", disabled: false },
    ];

    // Get all authors from the current list
    const currentListAuthors = computed(() => {
      const currentList = smartListsStore.currentList;
      if (!currentList?.listSources) return [];

      const authors = new Set();
      currentList.listSources.forEach((source) => {
        if (source.filters?.authors) {
          source.filters.authors.forEach((author) => {
            // Remove @ prefix if present for consistent display
            const cleanAuthor = author.replace(/^@/, "");
            authors.add(cleanAuthor);
          });
        }
      });

      return Array.from(authors);
    });

    // Determine if this list contains Twitter sources
    const isTwitterSource = computed(() => {
      const currentList = smartListsStore.currentList;
      if (!currentList?.listSources) return false;

      return currentList.listSources.some(
        (source) => source.dataSourceId === "twitter",
      );
    });

    // Authors to display (collapsed or expanded)
    const displayedAuthors = computed(() => {
      if (authorsExpanded.value || currentListAuthors.value.length <= 5) {
        return currentListAuthors.value;
      }
      return currentListAuthors.value.slice(0, 5);
    });

    const toggleAuthorsExpanded = () => {
      authorsExpanded.value = !authorsExpanded.value;
    };

    const openTwitterProfile = (handle) => {
      const cleanHandle = handle.replace(/^@/, "");
      window.open(`https://twitter.com/${cleanHandle}`, "_blank");
    };

    const isAuthorLoading = (author) => {
      return isTwitterSource.value && authorTweetCounts.value[author] === 0;
    };

    const checkAuthorTweetCounts = async () => {
      if (!currentListAuthors.value.length || !isTwitterSource.value) {
        return;
      }

      try {
        const response = await apiClient.getTweetCounts(
          currentListAuthors.value,
        );
        authorTweetCounts.value = response.tweet_counts;
      } catch (error) {
        console.error("Error checking author tweet counts:", error);
      }
    };

    const startPolling = () => {
      if (pollingInterval.value) {
        clearInterval(pollingInterval.value);
      }

      // Check if there are any authors with 0 tweets that need polling
      const hasLoadingAuthors = currentListAuthors.value.some(
        (author) => authorTweetCounts.value[author] === 0,
      );

      if (hasLoadingAuthors && isTwitterSource.value) {
        pollingInterval.value = setInterval(async () => {
          await checkAuthorTweetCounts();

          // Stop polling if all authors have tweets
          const stillLoading = currentListAuthors.value.some(
            (author) => authorTweetCounts.value[author] === 0,
          );

          if (!stillLoading) {
            clearInterval(pollingInterval.value);
            pollingInterval.value = null;
          }
        }, 15000); // 15 seconds
      }
    };

    const stopPolling = () => {
      if (pollingInterval.value) {
        clearInterval(pollingInterval.value);
        pollingInterval.value = null;
      }
    };

    // Watch for changes in current list and check tweet counts
    watch(
      () => smartListsStore.currentListId,
      async (newListId) => {
        // Reset state when switching lists
        authorTweetCounts.value = {};
        stopPolling();

        if (
          newListId &&
          currentListAuthors.value.length > 0 &&
          isTwitterSource.value
        ) {
          await checkAuthorTweetCounts();
          startPolling();
        }
      },
      { immediate: true },
    );

    // Also watch for changes in the authors themselves
    watch(
      currentListAuthors,
      async (newAuthors) => {
        if (newAuthors.length > 0 && isTwitterSource.value) {
          await checkAuthorTweetCounts();
          startPolling();
        } else {
          stopPolling();
        }
      },
      { immediate: true },
    );

    // Cleanup on unmount
    onUnmounted(() => {
      stopPolling();
    });

    const getViewButtonClass = (view) => {
      const baseClass =
        "px-3 py-1 text-sm font-medium rounded-md transition-colors";
      if (view.disabled) {
        return `${baseClass} text-gray-400 cursor-not-allowed`;
      }
      if (view.id === smartListsStore.currentView) {
        return `${baseClass} bg-white text-gray-900 shadow-sm`;
      }
      return `${baseClass} text-gray-600 hover:text-gray-900`;
    };

    const handleViewChange = (view) => {
      if (view.disabled) return;

      if (view.id === "ask") {
        // Toggle chat panel instead of just opening it
        if (chatStore.isChatPanelOpen) {
          chatStore.closeChatPanel();
        } else {
          chatStore.setHighlighted(true);
          chatStore.openChatPanel(); // Open the chat panel
          chatStore.startNewChat(); // Start a new chat when clicking Ask
          chatStore.focusInput(); // Signal to focus the input
          // Reset highlight after 2 seconds
          setTimeout(() => {
            chatStore.setHighlighted(false);
          }, 2000);
        }
        return; // Don't change the view, keep showing the feed
      }

      // Close chat panel when switching to other views
      if (chatStore.isChatPanelOpen) {
        chatStore.closeChatPanel();
      }

      smartListsStore.setCurrentView(view.id);
    };

    return {
      smartListsStore,
      chatStore,
      views,
      getViewButtonClass,
      handleViewChange,
      currentListAuthors,
      displayedAuthors,
      isTwitterSource,
      authorsExpanded,
      toggleAuthorsExpanded,
      openTwitterProfile,
      isAuthorLoading,
      authorTweetCounts,
    };
  },
};
</script>
