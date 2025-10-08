<template>
  <div class="space-y-3">
    <div
      v-for="list in lists"
      :key="list.id"
      class="p-4 bg-white rounded-lg border border-gray-200 hover:border-gray-300 transition-colors"
      :class="{ 'opacity-60': shouldGreyOutList(list) }"
    >
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-3 flex-1 min-w-0">
          <img
            :src="`https://ui-avatars.com/api/?name=${encodeURIComponent(
              list.name,
            )}&size=40&background=random&color=fff`"
            :alt="list.name"
            class="w-10 h-10 rounded-full flex-shrink-0"
          />
          <div
            class="flex-1 min-w-0"
            :class="{ 'cursor-pointer': clickable }"
            @click="clickable ? handleClick(list.id) : null"
          >
            <div class="flex items-center gap-2">
              <h3 class="text-sm font-medium text-gray-900 truncate">
                {{ list.name }}
              </h3>
              <span
                v-if="isCommunityList(list)"
                class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600"
              >
                Community
              </span>
            </div>
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
        </div>

        <div class="ml-4 flex-shrink-0 flex gap-2">
          <!-- Follow button for community lists OR unfollowed owned lists -->
          <button
            v-if="shouldShowFollowButton(list.id)"
            @click="handleFollow(list.id)"
            :disabled="loading"
            class="inline-flex items-center px-3 py-1.5 text-xs font-medium rounded-md text-blue-600 bg-blue-50 hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 transition-colors"
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

          <!-- Unfollow button for followed lists in "Your Lists" context -->
          <button
            v-if="showYourLists && isListFollowed(list.id)"
            @click="handleUnfollow(list.id)"
            :disabled="loading"
            class="inline-flex items-center px-3 py-1.5 text-xs font-medium rounded-md text-gray-600 bg-gray-50 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-500 disabled:opacity-50 transition-colors"
          >
            <span v-if="!loading">Unfollow</span>
            <svg
              v-else
              class="animate-spin h-3 w-3 text-gray-600"
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
            v-if="showDeleteButton && !isCommunityList(list)"
            @click="handleDelete(list.id)"
            :disabled="loading"
            class="inline-flex items-center px-3 py-1.5 text-xs font-medium rounded-md text-red-600 bg-red-50 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50 transition-colors"
          >
            <span v-if="!loading">Delete</span>
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
import { useUserStore } from "../stores/userStore";
import posthog from "posthog-js";

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
    showDeleteButton: {
      type: Boolean,
      default: false,
    },
    showOwnedLists: {
      type: Boolean,
      default: false,
    },
    showYourLists: {
      type: Boolean,
      default: false,
    },
    followedListIds: {
      type: Array,
      default: () => [],
    },
    clickable: {
      type: Boolean,
      default: false,
    },
  },
  emits: ["follow", "unfollow", "delete", "click"],
  setup(props, { emit }) {
    const loading = ref(false);
    const userStore = useUserStore();

    const getAuthorsFromList = (list) => {
      if (!list.listSources || !list.listSources.length) return [];

      // Get authors from first data source
      const firstSource = list.listSources[0];
      if (firstSource.filters && firstSource.filters.authors) {
        return firstSource.filters.authors.slice(0, 3); // Show max 3 authors
      }
      return [];
    };

    const isCommunityList = (list) => {
      // A community list is one that has an owner_email that is not the current user's
      const currentUserEmail = userStore.userEmail || "dev@example.com";
      return list.owner_email && list.owner_email !== currentUserEmail;
    };

    const shouldShowFollowButton = (listId) => {
      return !isListFollowed(listId);
    };
    const isListFollowed = (listId) => {
      return props.followedListIds.includes(listId);
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

    const handleDelete = async (listId) => {
      loading.value = true;
      try {
        emit("delete", listId);
      } finally {
        loading.value = false;
      }
    };

    const handleClick = (listId) => {
      const list = props.lists.find((l) => l.id === listId);

      // Track list navigation in PostHog
      if (typeof posthog !== "undefined" && posthog.__loaded) {
        posthog.capture("list_navigated", {
          list_id: listId,
          list_name: list?.name,
          is_community_list: isCommunityList(list),
          authors: getAuthorsFromList(list),
          item_count: list?.itemCount,
        });
      }

      emit("click", listId);
    };

    const shouldGreyOutList = (list) => {
      // Only grey out owned lists that aren't followed
      // Never grey out community lists (even when they appear in "Your Lists" because they're followed)
      const currentUserEmail = userStore.userEmail || "dev@example.com";
      const isOwned = list.owner_email === currentUserEmail;
      const isFollowed = props.followedListIds.includes(list.id);

      return isOwned && !isFollowed;
    };

    return {
      loading,
      getAuthorsFromList,
      isCommunityList,
      isListFollowed,
      shouldShowFollowButton,
      shouldGreyOutList,
      handleFollow,
      handleUnfollow,
      handleDelete,
      handleClick,
    };
  },
};
</script>
