<template>
  <div class="h-full flex flex-col">
    <!-- Always show content structure -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <!-- Content Summary -->
      <div class="p-4 bg-blue-50 border-b border-blue-100 mb-0">
        <div class="flex items-center justify-between mb-2">
          <h3 class="text-sm font-medium text-blue-900">Feed Summary</h3>
          <div
            v-if="smartListsStore.currentListDateRange"
            class="text-xs text-blue-700 bg-blue-100 px-2 py-1 rounded-full"
          >
            {{ formatDateRange(smartListsStore.currentListDateRange) }}
          </div>
        </div>
        <div class="text-sm text-blue-800 leading-relaxed">
          <div
            v-if="
              smartListsStore.currentListSummary &&
              (typeof smartListsStore.currentListSummary === 'string' ||
                smartListsStore.currentListSummary.status === 'completed')
            "
          >
            <div
              v-for="(bullet, index) in getDisplayedBullets()"
              :key="index"
              class="mb-1 cursor-pointer hover:text-blue-900 hover:bg-blue-100 px-1 py-0.5 rounded transition-colors"
              @click="handleBulletClick(bullet, index)"
              v-html="formatBulletWithReferences(bullet)"
            ></div>
            <div v-if="shouldShowReadMore()" class="mt-3">
              <button
                @click="toggleExpanded"
                class="text-xs text-blue-600 hover:text-blue-800 hover:bg-blue-100 px-2 py-1 rounded-md transition-colors font-medium"
              >
                {{ isExpanded ? "Read less" : "Read more" }}
              </button>
            </div>
          </div>
          <div
            v-else-if="
              smartListsStore.currentListSummary &&
              smartListsStore.currentListSummary.status === 'generating'
            "
            class="text-blue-600 italic"
          >
            Generating summary...
          </div>
          <div
            v-else-if="
              smartListsStore.currentListSummary &&
              smartListsStore.currentListSummary.status === 'error'
            "
            class="text-red-600 italic"
          >
            Failed to generate summary
          </div>
          <div v-else class="text-blue-600 italic">Generating summary...</div>
        </div>
      </div>

      <!-- Settings Panel (Collapsable) -->
      <div class="bg-white border-b border-gray-200">
        <button
          @click="toggleSettings"
          class="w-full px-4 py-3 flex items-center gap-2 hover:bg-gray-50 transition-colors"
        >
          <svg
            class="w-5 h-5 text-gray-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
            />
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
            />
          </svg>
          <svg
            class="w-4 h-4 text-gray-500 transition-transform"
            :class="{ 'rotate-180': settingsExpanded }"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </button>

        <div v-if="settingsExpanded" class="px-4 pb-4 pt-3 space-y-3">
          <!-- RAG Query -->
          <div>
            <label class="block text-xs font-medium text-gray-600 mb-1">
              RAG Query
            </label>
            <input
              v-model="localRagQuery"
              @keyup.enter="saveSettings"
              type="text"
              class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter search query..."
            />
          </div>

          <!-- Reranking Threshold -->
          <div class="flex items-center gap-2">
            <label class="text-xs font-medium text-gray-600 flex-shrink-0">
              Reranking Threshold
            </label>
            <input
              v-model.number="localRerankingThreshold"
              @keyup.enter="saveSettings"
              type="number"
              step="0.01"
              min="0"
              max="1"
              class="w-20 px-2 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              :placeholder="defaultRerankingThreshold.toString()"
            />
          </div>

          <!-- Item count display -->
          <div class="text-xs text-gray-600">
            Showing
            <span class="font-semibold">{{ sortedItems.length }}</span> item{{
              sortedItems.length !== 1 ? "s" : ""
            }}
            with threshold ≥ {{ savedRerankingThreshold }}
          </div>

          <!-- Save button with status -->
          <div class="flex items-center gap-3">
            <button
              @click="saveSettings"
              :disabled="!hasSettingsChanged"
              class="px-6 py-2 text-sm font-medium rounded-lg transition-colors"
              :class="
                hasSettingsChanged
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              "
            >
              Save
            </button>

            <!-- Status indicator -->
            <div
              v-if="isThresholdChangePending"
              class="flex items-center gap-2 text-xs text-blue-600"
            >
              <svg class="animate-spin h-3 w-3" fill="none" viewBox="0 0 24 24">
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
              <span>Updating filters...</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Sorting Panel -->
      <div class="px-4 py-3 bg-white border-b border-gray-200">
        <div class="flex items-center gap-3">
          <span class="text-sm font-medium text-gray-700">Sort by:</span>
          <div class="flex bg-gray-100 rounded-lg p-1">
            <button
              @click="setSortMethod('date')"
              :class="[
                'px-3 py-1.5 text-sm font-medium rounded-md transition-all duration-200',
                sortMethod === 'date'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50',
              ]"
            >
              Date
            </button>
            <button
              @click="setSortMethod('similarity')"
              :class="[
                'px-3 py-1.5 text-sm font-medium rounded-md transition-all duration-200',
                sortMethod === 'similarity'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50',
              ]"
            >
              Similarity
            </button>
          </div>
        </div>
      </div>

      <!-- Tweet List -->
      <div class="flex-1 overflow-y-auto relative">
        <!-- Loading overlay for tweet list only -->
        <div
          v-if="
            smartListsStore.isCurrentListLoading ||
            isWaitingForTweets ||
            isRequerying
          "
          class="absolute inset-0 flex items-center justify-center bg-white bg-opacity-75 z-10"
        >
          <div class="text-center">
            <div
              class="inline-flex items-center px-4 py-2 font-semibold leading-6 text-sm shadow rounded-md text-blue-500 bg-white transition ease-in-out duration-150"
            >
              <svg
                class="animate-spin -ml-1 mr-3 h-5 w-5 text-blue-500"
                xmlns="http://www.w3.org/2000/svg"
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
              {{ currentLoadingMessage }}
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div
          v-if="
            !smartListsStore.isCurrentListLoading &&
            !isRequerying &&
            smartListsStore.currentListItems.length === 0
          "
          class="flex items-center justify-center h-full"
        >
          <div class="text-center">
            <div
              class="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center"
            >
              <svg
                class="w-8 h-8 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M7 4V2a1 1 0 011-1h8a1 1 0 011 1v2M7 4h10l1 14H6l1-14zM10 7v2m4-2v2"
                ></path>
              </svg>
            </div>
            <p class="text-gray-500 mb-2">No tweets found</p>
            <p class="text-sm text-gray-400">
              This list may still be fetching tweets from the network
            </p>
          </div>
        </div>

        <!-- Tweet items -->
        <div v-else class="divide-y divide-gray-200">
          <component
            v-for="item in sortedItems"
            :key="item.id"
            :is="getComponentForType(item.type)"
            :item="item"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { onMounted, watch, ref, computed, onUnmounted, inject } from "vue";
import { useSmartListsStore } from "../stores/smartListsStore";
import { apiClient } from "../api/client";
import TweetItem from "./TweetItem.vue";

export default {
  name: "FeedView",
  components: {
    TweetItem,
  },
  setup() {
    const smartListsStore = useSmartListsStore();
    const isExpanded = ref(false);
    const maxBulletsCollapsed = 3;
    const sortMethod = ref("date");
    const loadingMessage = ref("Loading tweets...");
    let loadingMessageInterval = null;

    // Get allTweetCountsZero from parent (MiddlePanel)
    const allTweetCountsZero = inject("allTweetCountsZero", ref(false));

    // Settings state
    const settingsExpanded = ref(false);
    const localRagQuery = ref("");
    const savedRagQuery = ref("");
    const localRerankingThreshold = ref(null);
    const savedRerankingThreshold = ref(null);
    const defaultRerankingThreshold = ref(0.82);

    // Track the thresholds used for the last backend query
    const lastQueriedRerankingThreshold = ref(null);

    // Loading state for threshold changes
    const isRequerying = ref(false);
    const isThresholdChangePending = ref(false);

    // Check if settings have changed
    const hasSettingsChanged = computed(() => {
      const thresholdChanged =
        Number(
          localRerankingThreshold.value ?? defaultRerankingThreshold.value,
        ) !==
        Number(
          savedRerankingThreshold.value ?? defaultRerankingThreshold.value,
        );
      const ragQueryChanged =
        (localRagQuery.value || "") !== (savedRagQuery.value || "");
      return thresholdChanged || ragQueryChanged;
    });

    // Computed to check if we should show loading state for waiting tweets
    const isWaitingForTweets = computed(() => {
      return (
        allTweetCountsZero.value &&
        smartListsStore.currentListItems.length === 0 &&
        !smartListsStore.isCurrentListLoading
      );
    });

    // Combined loading message
    const currentLoadingMessage = computed(() => {
      if (smartListsStore.isCurrentListLoading) {
        return loadingMessage.value;
      } else if (isWaitingForTweets.value) {
        return "Waiting for tweets to be fetched...";
      }
      return loadingMessage.value;
    });

    // Generate summary when list changes
    watch(
      () => smartListsStore.currentListId,
      async (newListId) => {
        if (newListId && !smartListsStore.summariesCache[newListId]) {
          try {
            const result = await smartListsStore.generateSummary(newListId);

            // If it's generating, start polling
            if (result.status === "generating") {
              smartListsStore.pollSummaryStatus(newListId, (updatedResult) => {
                // The store will automatically update the cache, which will trigger reactivity
              });
            }
          } catch (error) {
            console.error("Failed to generate summary:", error);
          }
        }
      },
      { immediate: true },
    );

    const getComponentForType = (type) => {
      const componentMap = {
        tweet: "TweetItem",
        // Future types can be added here:
        // 'article': 'ArticleItem',
        // 'video': 'VideoItem'
      };

      return componentMap[type] || "TweetItem"; // Default to TweetItem
    };

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

    const getSummaryBullets = (summaryData) => {
      if (!summaryData) return [];

      // Handle both old string format and new object format
      const summaryText =
        typeof summaryData === "string" ? summaryData : summaryData.summary;

      if (!summaryText) return [];
      return summaryText
        .split("\n")
        .filter((line) => line.trim().startsWith("•"));
    };

    const handleBulletClick = (bullet, index) => {
      // Placeholder for future functionality
      console.log(`Clicked bullet ${index + 1}:`, bullet);
    };

    const formatBulletWithReferences = (bullet) => {
      // Find references in the format [1,2,3] at the end of the bullet
      const referencePattern = /(\[[\d,\s]+\])$/;
      const match = bullet.match(referencePattern);

      let text = match ? bullet.replace(referencePattern, "") : bullet;

      // Format markdown bold text
      text = text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

      if (match) {
        const references = match[1];
        return `${text} <span class="text-xs text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded-md ml-1 font-mono">${references}</span>`;
      }

      return text;
    };

    const getDisplayedBullets = () => {
      const allBullets = getSummaryBullets(smartListsStore.currentListSummary);
      if (isExpanded.value || allBullets.length <= maxBulletsCollapsed) {
        return allBullets;
      }
      return allBullets.slice(0, maxBulletsCollapsed);
    };

    const shouldShowReadMore = () => {
      const allBullets = getSummaryBullets(smartListsStore.currentListSummary);
      return allBullets.length > maxBulletsCollapsed;
    };

    const toggleExpanded = () => {
      isExpanded.value = !isExpanded.value;
    };

    // Initialize settings from current list
    const initializeThresholdsFromList = () => {
      const currentList = smartListsStore.currentList;
      if (currentList?.listSources && currentList.listSources.length > 0) {
        // Get settings from the first source (assuming all sources have same settings)
        const filters = currentList.listSources[0].filters;
        const dbThreshold = filters?.reranking_threshold || 0.82;
        const dbRagQuery = filters?.ragQuery || "";

        defaultRerankingThreshold.value = dbThreshold;
        localRerankingThreshold.value = dbThreshold;
        savedRerankingThreshold.value = dbThreshold;
        localRagQuery.value = dbRagQuery;
        savedRagQuery.value = dbRagQuery;

        // Set last queried to the DB value since that's what was used to fetch the current items
        // The backend used this threshold to fetch the items we're now seeing
        lastQueriedRerankingThreshold.value = dbThreshold;
        console.log("Initialized settings:", {
          ragQuery: dbRagQuery,
          threshold: dbThreshold,
        });
      }
    };

    // Watch for list changes to initialize thresholds
    watch(
      () => smartListsStore.currentListId,
      () => {
        initializeThresholdsFromList();
      },
      { immediate: true },
    );

    const toggleSettings = () => {
      settingsExpanded.value = !settingsExpanded.value;
    };

    const saveSettings = async () => {
      if (!hasSettingsChanged.value) return;

      isThresholdChangePending.value = true;
      try {
        await applySettingsChange();
        savedRerankingThreshold.value = localRerankingThreshold.value;
        savedRagQuery.value = localRagQuery.value;
      } finally {
        isThresholdChangePending.value = false;
      }
    };

    const applySettingsChange = async () => {
      // Ensure we have numbers, not strings
      const newReranking = Number(
        localRerankingThreshold.value ?? defaultRerankingThreshold.value,
      );
      const newRagQuery = localRagQuery.value || "";
      const lastQueried = Number(lastQueriedRerankingThreshold.value);

      // Check if RAG query changed
      const ragQueryChanged = newRagQuery !== savedRagQuery.value;

      console.log("Applying settings change:", {
        newReranking,
        newRagQuery,
        lastQueried,
        ragQueryChanged,
        needsRequery: newReranking < lastQueried || ragQueryChanged,
      });

      // Always requery if we don't have a last queried value
      if (
        lastQueriedRerankingThreshold.value === null ||
        lastQueriedRerankingThreshold.value === undefined
      ) {
        console.log("No last queried value, skipping for now");
        lastQueriedRerankingThreshold.value = newReranking;
        return;
      }

      const listId = smartListsStore.currentListId;
      if (!listId) return;

      // Update the settings in the database
      try {
        console.log("Updating settings in database:", {
          newReranking,
          newRagQuery,
        });
        await apiClient.updateListThreshold(listId, newReranking, newRagQuery);

        // Update in local store
        const currentList = smartListsStore.currentList;
        if (currentList?.listSources) {
          for (const source of currentList.listSources) {
            source.filters.reranking_threshold = newReranking;
            source.filters.ragQuery = newRagQuery;
          }
        }
      } catch (error) {
        console.error("Failed to update settings in database:", error);
        return;
      }

      // Check if we need to requery the backend
      // We need to requery if:
      // 1. The new threshold is LOWER than what we last queried, OR
      // 2. The RAG query changed
      const needsRequery = newReranking < lastQueried || ragQueryChanged;

      if (needsRequery) {
        console.log("Requerying backend with new settings");
        // Need to requery backend with new settings
        isRequerying.value = true;
        try {
          // Refresh items from backend
          await smartListsStore.refreshComputedItems(listId);

          // Update last queried threshold to the new value
          lastQueriedRerankingThreshold.value = newReranking;
          console.log(
            "Requery complete, updated lastQueried to:",
            newReranking,
          );
        } finally {
          isRequerying.value = false;
        }
      } else {
        console.log("Filtering locally, no requery needed");
        // Can filter locally - items with lower thresholds were already fetched
        // The sortedItems computed will handle filtering
        // No need to update lastQueriedRerankingThreshold since we're just filtering locally
      }
    };

    const sortedItems = computed(() => {
      let items = [...smartListsStore.currentListItems];

      // Filter by saved reranking threshold (only after save)
      const currentReranking =
        savedRerankingThreshold.value ?? defaultRerankingThreshold.value;

      // Apply filtering based on thresholds
      // If there's a RAG query, filter by reranking score
      const hasRagQuery = smartListsStore.currentList?.listSources?.some(
        (source) => source.filters?.ragQuery && source.filters.ragQuery.trim(),
      );

      if (hasRagQuery && currentReranking > 0) {
        items = items.filter((item) => {
          const score = item.similarity_score;
          // Only filter items that have a similarity score
          // Items without scores (no RAG query) should always be included
          if (score !== null && score !== undefined) {
            return score >= currentReranking;
          }
          return true;
        });
      }

      if (sortMethod.value === "similarity") {
        return items.sort((a, b) => {
          const scoreA = a.similarity_score || 0;
          const scoreB = b.similarity_score || 0;
          return scoreB - scoreA; // Descending order (highest similarity first)
        });
      } else {
        // Sort by date (default)
        return items.sort((a, b) => {
          const dateA = new Date(a.timestamp);
          const dateB = new Date(b.timestamp);
          return dateB - dateA; // Descending order (newest first)
        });
      }
    });

    const setSortMethod = (method) => {
      sortMethod.value = method;
    };

    // Update loading message based on elapsed time
    const updateLoadingMessage = () => {
      if (!smartListsStore.isCurrentListLoading) {
        loadingMessage.value = "Loading tweets...";
        return;
      }

      const startTime = smartListsStore.getCurrentListLoadingStartTime;
      if (!startTime) {
        loadingMessage.value = "Loading tweets...";
        return;
      }

      const elapsed = Date.now() - startTime;

      if (elapsed < 2000) {
        loadingMessage.value = "Fetching data from your sources";
      } else {
        loadingMessage.value = "Computing relevance";
      }
    };

    // Watch for loading state changes
    watch(
      () => smartListsStore.isCurrentListLoading,
      (isLoading) => {
        if (isLoading) {
          updateLoadingMessage();
          loadingMessageInterval = setInterval(updateLoadingMessage, 500); // Update every 500ms
        } else {
          if (loadingMessageInterval) {
            clearInterval(loadingMessageInterval);
            loadingMessageInterval = null;
          }
        }
      },
      { immediate: true },
    );

    // Cleanup interval on unmount
    onUnmounted(() => {
      if (loadingMessageInterval) {
        clearInterval(loadingMessageInterval);
      }
    });

    return {
      smartListsStore,
      getComponentForType,
      formatDateRange,
      getSummaryBullets,
      handleBulletClick,
      formatBulletWithReferences,
      getDisplayedBullets,
      shouldShowReadMore,
      toggleExpanded,
      isExpanded,
      sortMethod,
      sortedItems,
      setSortMethod,
      loadingMessage,
      isWaitingForTweets,
      currentLoadingMessage,
      settingsExpanded,
      toggleSettings,
      localRagQuery,
      savedRagQuery,
      localRerankingThreshold,
      savedRerankingThreshold,
      defaultRerankingThreshold,
      saveSettings,
      hasSettingsChanged,
      isRequerying,
      isThresholdChangePending,
    };
  },
};
</script>
