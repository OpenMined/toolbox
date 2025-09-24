<template>
  <div class="space-y-3">
    <div
      v-for="list in lists"
      :key="list.id"
      class="p-4 bg-white rounded-lg border border-gray-200 hover:border-gray-300 transition-colors"
    >
      <div class="flex items-center justify-between">
        <div class="flex-1 min-w-0">
          <h3 class="text-sm font-medium text-gray-900 truncate">
            {{ list.name }}
          </h3>
          <div class="mt-1 flex flex-wrap gap-1">
            <span
              v-for="author in getAuthorsFromList(list)"
              :key="author"
              class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
            >
              {{ author }}
            </span>
          </div>
          <p class="mt-1 text-xs text-gray-500">{{ list.itemCount }} items</p>
        </div>

        <div class="ml-4 flex-shrink-0">
          <button
            v-if="showFollowButton"
            @click="handleFollow(list.id)"
            :disabled="loading"
            class="inline-flex items-center px-3 py-1.5 border border-blue-300 text-xs font-medium rounded-md text-blue-700 bg-white hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          >
            <span v-if="!loading">Follow</span>
            <svg
              v-else
              class="animate-spin h-3 w-3 text-blue-600"
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
          </button>

          <button
            v-if="showUnfollowButton"
            @click="handleUnfollow(list.id)"
            :disabled="loading"
            class="inline-flex items-center px-3 py-1.5 border border-red-300 text-xs font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50"
          >
            <span v-if="!loading">Unfollow</span>
            <svg
              v-else
              class="animate-spin h-3 w-3 text-red-600"
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
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from "vue";

export default {
  name: "SmartListListView",
  props: {
    lists: {
      type: Array,
      required: true,
    },
    showFollowButton: {
      type: Boolean,
      default: false,
    },
    showUnfollowButton: {
      type: Boolean,
      default: false,
    },
  },
  emits: ["follow", "unfollow"],
  setup(props, { emit }) {
    const loading = ref(false);

    const getAuthorsFromList = (list) => {
      if (!list.listSources || !list.listSources.length) return [];

      // Get authors from first data source
      const firstSource = list.listSources[0];
      if (firstSource.filters && firstSource.filters.authors) {
        return firstSource.filters.authors.slice(0, 3); // Show max 3 authors
      }
      return [];
    };

    const handleFollow = async (listId) => {
      loading.value = true;
      try {
        emit("follow", listId);
      } finally {
        loading.value = false;
      }
    };

    const handleUnfollow = async (listId) => {
      loading.value = true;
      try {
        emit("unfollow", listId);
      } finally {
        loading.value = false;
      }
    };

    return {
      loading,
      getAuthorsFromList,
      handleFollow,
      handleUnfollow,
    };
  },
};
</script>
