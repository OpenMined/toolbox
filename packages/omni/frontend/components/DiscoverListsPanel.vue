<template>
  <div class="h-full flex flex-col bg-gray-50">
    <!-- Header - Full Width -->
    <div class="bg-white border-b border-gray-200 px-6 py-4">
      <div class="flex items-center justify-between">
        <h1 class="text-lg font-semibold text-gray-900">Discover Lists</h1>
        <button
          @click="closePanelAndShowWelcome"
          class="text-gray-400 hover:text-gray-600"
        >
          <span class="sr-only">Close</span>
          <svg
            class="h-6 w-6"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>
    </div>

    <!-- Content Container - Left Aligned with Max Width -->
    <div class="flex-1 flex">
      <div class="w-full max-w-2xl flex flex-col">
        <!-- Content -->
        <div class="flex-1 overflow-auto px-6 py-6 space-y-8">
          <!-- Discover New Lists Section -->
          <div>
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-base font-medium text-gray-900">
                Discover New Lists
              </h2>
              <span class="text-sm text-gray-500"
                >{{ notFollowingLists.length }} available</span
              >
            </div>

            <div v-if="loadingNotFollowing" class="text-center py-8">
              <div
                class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"
              ></div>
              <p class="mt-2 text-sm text-gray-500">Loading lists...</p>
            </div>

            <div
              v-else-if="displayedNotFollowingLists.length === 0"
              class="text-center py-8"
            >
              <p class="text-sm text-gray-500">
                You're following all available lists!
              </p>
            </div>

            <div v-else>
              <SmartListListView
                :lists="displayedNotFollowingLists"
                :show-follow-button="true"
                @follow="handleFollowList"
              />

              <div v-if="canShowMoreNotFollowing" class="mt-4 text-center">
                <button
                  @click="showMoreNotFollowing"
                  :disabled="loadingMore"
                  class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                >
                  <span v-if="!loadingMore">Show More</span>
                  <span v-else class="flex items-center">
                    <svg
                      class="animate-spin -ml-1 mr-2 h-4 w-4"
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
                    Loading...
                  </span>
                </button>
              </div>
            </div>
          </div>

          <!-- Your Lists Section -->
          <div>
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-base font-medium text-gray-900">Your Lists</h2>
              <span class="text-sm text-gray-500"
                >{{ followedLists.length }} followed</span
              >
            </div>

            <div v-if="loadingFollowed" class="text-center py-8">
              <div
                class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"
              ></div>
              <p class="mt-2 text-sm text-gray-500">Loading your lists...</p>
            </div>

            <div
              v-else-if="followedLists.length === 0"
              class="text-center py-8"
            >
              <p class="text-sm text-gray-500">
                You haven't followed any lists yet.
              </p>
            </div>

            <div v-else>
              <SmartListListView
                :lists="followedLists"
                :show-unfollow-button="true"
                @unfollow="handleUnfollowList"
              />
            </div>
          </div>

          <!-- New List Button -->
          <div class="pt-4 border-t border-gray-200">
            <button
              @click="showCreateList"
              class="inline-flex items-center text-sm font-medium text-blue-600 hover:text-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded-md px-2 py-1 hover:bg-blue-50 transition-colors"
            >
              <svg
                class="mr-2 h-4 w-4"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 6v6m0 0v6m0-6h6m-6 0H6"
                />
              </svg>
              Create New List
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from "vue";
import { useDataSourcesStore } from "../stores/dataSourcesStore";
import { useSmartListsStore } from "../stores/smartListsStore";
import { useUserStore } from "../stores/userStore";
import { apiClient } from "../api/client.js";
import SmartListListView from "./SmartListListView.vue";

export default {
  name: "DiscoverListsPanel",
  components: {
    SmartListListView,
  },
  setup() {
    const dataSourcesStore = useDataSourcesStore();
    const smartListsStore = useSmartListsStore();
    const userStore = useUserStore();

    const notFollowingLists = ref([]);
    const followedLists = ref([]);
    const loadingNotFollowing = ref(false);
    const loadingFollowed = ref(false);
    const loadingMore = ref(false);
    const displayLimit = ref(5);

    const displayedNotFollowingLists = computed(() => {
      return notFollowingLists.value.slice(0, displayLimit.value);
    });

    const canShowMoreNotFollowing = computed(() => {
      return notFollowingLists.value.length > displayLimit.value;
    });

    const fetchNotFollowingLists = async () => {
      loadingNotFollowing.value = true;
      try {
        const userEmail = userStore.userEmail || "dev@example.com";
        notFollowingLists.value = await apiClient.getNotFollowingSmartLists(
          userEmail,
        );
      } catch (error) {
        console.error("Failed to fetch not following lists:", error);
      } finally {
        loadingNotFollowing.value = false;
      }
    };

    const fetchFollowedLists = async () => {
      loadingFollowed.value = true;
      try {
        const userEmail = userStore.userEmail || "dev@example.com";
        followedLists.value = await apiClient.getFollowedSmartLists(userEmail);
      } catch (error) {
        console.error("Failed to fetch followed lists:", error);
      } finally {
        loadingFollowed.value = false;
      }
    };

    const showMoreNotFollowing = () => {
      loadingMore.value = true;
      setTimeout(() => {
        displayLimit.value += 10;
        loadingMore.value = false;
      }, 300);
    };

    const handleFollowList = async (listId) => {
      try {
        const userEmail = userStore.userEmail || "dev@example.com";
        await apiClient.followSmartList(listId, userEmail);

        // Move list from not following to followed
        const listIndex = notFollowingLists.value.findIndex(
          (list) => list.id === listId,
        );
        if (listIndex !== -1) {
          const followedList = notFollowingLists.value.splice(listIndex, 1)[0];
          followedLists.value.push(followedList);
        }

        // Refresh the sidebar lists
        await smartListsStore.fetchSmartLists();
      } catch (error) {
        console.error("Failed to follow list:", error);
      }
    };

    const handleUnfollowList = async (listId) => {
      try {
        const userEmail = userStore.userEmail || "dev@example.com";
        await apiClient.unfollowSmartList(listId, userEmail);

        // Move list from followed to not following
        const listIndex = followedLists.value.findIndex(
          (list) => list.id === listId,
        );
        if (listIndex !== -1) {
          const unfollowedList = followedLists.value.splice(listIndex, 1)[0];
          notFollowingLists.value.unshift(unfollowedList);
        }

        // Refresh the sidebar lists
        await smartListsStore.fetchSmartLists();
      } catch (error) {
        console.error("Failed to unfollow list:", error);
      }
    };

    const showCreateList = () => {
      dataSourcesStore.setDashboardView("CreateList");
    };

    const closePanelAndShowWelcome = () => {
      dataSourcesStore.closeDashboard();
      smartListsStore.currentListId = null;
    };

    onMounted(async () => {
      await Promise.all([fetchNotFollowingLists(), fetchFollowedLists()]);
    });

    return {
      notFollowingLists,
      followedLists,
      displayedNotFollowingLists,
      canShowMoreNotFollowing,
      loadingNotFollowing,
      loadingFollowed,
      loadingMore,
      showMoreNotFollowing,
      handleFollowList,
      handleUnfollowList,
      showCreateList,
      closePanelAndShowWelcome,
    };
  },
};
</script>
