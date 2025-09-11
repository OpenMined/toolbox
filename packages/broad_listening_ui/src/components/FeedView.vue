<template>
  <div class="h-full">
    <div
      v-if="listsStore.currentListItems.length === 0"
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
            v-if="listsStore.currentListDateRange"
            class="text-xs text-blue-700 bg-blue-100 px-2 py-1 rounded-full"
          >
            {{ formatDateRange(listsStore.currentListDateRange) }}
          </div>
        </div>
        <div class="text-sm text-blue-800 leading-relaxed">
          <div
            v-for="(bullet, index) in getSummaryBullets(
              listsStore.currentListSummary,
            )"
            :key="index"
            class="mb-1 cursor-pointer hover:text-blue-900 hover:bg-blue-100 px-1 py-0.5 rounded transition-colors"
            @click="handleBulletClick(bullet, index)"
            v-html="formatBulletWithReferences(bullet)"
          ></div>
        </div>
      </div>

      <!-- Tweet List -->
      <div class="divide-y divide-gray-200">
        <component
          v-for="item in listsStore.currentListItems"
          :key="item.id"
          :is="getComponentForType(item.type)"
          :item="item"
        />
      </div>
    </div>
  </div>
</template>

<script>
import { useListsStore } from "../stores/listsStore";
import TweetItem from "./TweetItem.vue";

export default {
  name: "FeedView",
  components: {
    TweetItem,
  },
  setup() {
    const listsStore = useListsStore();

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

    const getSummaryBullets = (summary) => {
      if (!summary) return [];
      return summary.split("\n").filter((line) => line.trim().startsWith("•"));
    };

    const handleBulletClick = (bullet, index) => {
      // Placeholder for future functionality
      console.log(`Clicked bullet ${index + 1}:`, bullet);
    };

    const formatBulletWithReferences = (bullet) => {
      // Find references in the format [1,2,3] at the end of the bullet
      const referencePattern = /(\[[\d,\s]+\])$/;
      const match = bullet.match(referencePattern);

      if (match) {
        const text = bullet.replace(referencePattern, "");
        const references = match[1];
        return `${text} <span class="text-xs text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded-md ml-1 font-mono">${references}</span>`;
      }

      return bullet;
    };

    return {
      listsStore,
      getComponentForType,
      formatDateRange,
      getSummaryBullets,
      handleBulletClick,
      formatBulletWithReferences,
    };
  },
};
</script>
