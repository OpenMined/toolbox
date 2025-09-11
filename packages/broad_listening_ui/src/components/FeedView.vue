<template>
  <div class="h-full">
    <div
      v-if="listsStore.currentListItems.length === 0"
      class="flex items-center justify-center h-full"
    >
      <p class="text-gray-500">No items in this list</p>
    </div>

    <div v-else class="divide-y divide-gray-200">
      <component
        v-for="item in listsStore.currentListItems"
        :key="item.id"
        :is="getComponentForType(item.type)"
        :item="item"
      />
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

    return {
      listsStore,
      getComponentForType,
    };
  },
};
</script>
