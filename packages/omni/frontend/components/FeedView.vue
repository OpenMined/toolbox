<template>
  <div class="h-full">
    <div
      v-if="smartListsStore.currentListItems.length === 0"
      class="flex items-center justify-center h-full"
    >
      <p class="text-gray-500">No items in this list</p>
    </div>

    <div v-else>
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
      <div class="divide-y divide-gray-200">
        <component
          v-for="item in sortedItems"
          :key="item.id"
          :is="getComponentForType(item.type)"
          :item="item"
        />
      </div>
    </div>
  </div>
</template>

<script>
import { onMounted, watch, ref, computed } from "vue";
import { useSmartListsStore } from "../stores/smartListsStore";
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

      const fromDate = new Date(dateRange.from);
      const toDate = new Date(dateRange.to);

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

    const sortedItems = computed(() => {
      const items = [...smartListsStore.currentListItems];

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
    };
  },
};
</script>
