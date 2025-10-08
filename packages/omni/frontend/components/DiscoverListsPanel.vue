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
          <!-- Your Lists Section (Lists you're following) -->
          <div>
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-base font-medium text-gray-900">Your Lists</h2>
              <span class="text-sm text-gray-500"
                >{{ yourLists.length }} lists</span
              >
            </div>

            <div v-if="loadingMyLists" class="text-center py-8">
              <div
                class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"
              ></div>
              <p class="mt-2 text-sm text-gray-500">Loading your lists...</p>
            </div>

            <div v-else-if="yourLists.length === 0" class="text-center py-8">
              <p class="text-sm text-gray-500">
                You haven't created or followed any lists yet.
              </p>
            </div>

            <div v-else>
              <SmartListListView
                :lists="yourLists"
                :show-unfollow-button="true"
                :show-delete-button="true"
                :show-your-lists="true"
                :followed-list-ids="followedListIds"
                @unfollow="handleUnfollowList"
                @delete="handleDeleteList"
              />
            </div>
          </div>

          <!-- Community Lists Section (Unfollowed community lists) -->
          <div>
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-base font-medium text-gray-900">
                Community Lists
              </h2>
              <span class="text-sm text-gray-500"
                >{{ displayedCommunityLists.length }} available</span
              >
            </div>

            <div v-if="loadingCommunityLists" class="text-center py-8">
              <div
                class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"
              ></div>
              <p class="mt-2 text-sm text-gray-500">
                Loading community lists...
              </p>
            </div>

            <div
              v-else-if="displayedCommunityLists.length === 0"
              class="text-center py-8"
            >
              <p class="text-sm text-gray-500">
                No unfollowed community lists available.
              </p>
            </div>

            <div v-else>
              <SmartListListView
                :lists="displayedCommunityLists"
                :show-follow-button="true"
                @follow="handleFollowList"
              />

              <div v-if="canShowMoreCommunityLists" class="mt-4 text-center">
                <button
                  @click="showMoreCommunityLists"
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

    const allLists = ref([]);
    const myOwnedLists = ref([]); // Lists I own (both followed and unfollowed)
    const followedListIds = ref([]); // IDs of lists I'm following
    const loadingAllLists = ref(false);
    const loadingMyOwnedLists = ref(false);
    const loadingFollowedIds = ref(false);
    const loadingMore = ref(false);
    const displayLimit = ref(5);

    // "Your Lists" = owned lists + followed community lists
    const yourLists = computed(() => {
      const currentUserEmail = userStore.userEmail || "dev@example.com";

      // Get all owned lists
      const ownedLists = myOwnedLists.value;

      // Get followed community lists (lists owned by others that you're following)
      const followedCommunityLists = allLists.value.filter(
        (list) =>
          list.owner_email !== currentUserEmail &&
          followedListIds.value.includes(list.id),
      );
      // 1. Owned lists that are followed
      const ownedFollowedLists = ownedLists.filter((list) =>
        followedListIds.value.includes(list.id),
      );
      // 2. Followed community lists (already computed above)
      // 3. Owned lists that are not followed
      const ownedUnfollowedLists = ownedLists.filter(
        (list) => !followedListIds.value.includes(list.id),
      );

      return [
        ...ownedFollowedLists,
        ...followedCommunityLists,
        ...ownedUnfollowedLists,
      ];

      // return [...ownedLists, ...followedCommunityLists];
    });

    const communityLists = computed(() => {
      // Community lists are unfollowed lists not created by current user
      const currentUserEmail = userStore.userEmail || "dev@example.com";

      return allLists.value.filter(
        (list) =>
          list.owner_email !== currentUserEmail &&
          !followedListIds.value.includes(list.id),
      );
    });

    const displayedCommunityLists = computed(() => {
      return communityLists.value.slice(0, displayLimit.value);
    });

    const canShowMoreCommunityLists = computed(() => {
      return communityLists.value.length > displayLimit.value;
    });

    const loadingCommunityLists = computed(() => {
      return loadingAllLists.value || loadingFollowedIds.value;
    });

    const loadingMyLists = computed(() => {
      return loadingMyOwnedLists.value || loadingFollowedIds.value;
    });

    const fetchAllLists = async () => {
      loadingAllLists.value = true;
      try {
        const userEmail = userStore.userEmail || "dev@example.com";
        allLists.value = await apiClient.getSmartLists(userEmail);
      } catch (error) {
        console.error("Failed to fetch all lists:", error);
      } finally {
        loadingAllLists.value = false;
      }
    };

    const fetchMyOwnedLists = async () => {
      loadingMyOwnedLists.value = true;
      try {
        const userEmail = userStore.userEmail || "dev@example.com";
        const lists = await apiClient.getMySmartLists(userEmail);
        myOwnedLists.value = lists;
      } catch (error) {
        console.error("Failed to fetch my owned lists:", error);
      } finally {
        loadingMyOwnedLists.value = false;
      }
    };

    const fetchFollowedListIds = async () => {
      loadingFollowedIds.value = true;
      try {
        const userEmail = userStore.userEmail || "dev@example.com";
        const followedLists = await apiClient.getFollowedSmartLists(userEmail);
        followedListIds.value = followedLists.map((list) => list.id);
      } catch (error) {
        console.error("Failed to fetch followed list IDs:", error);
      } finally {
        loadingFollowedIds.value = false;
      }
    };

    const showMoreCommunityLists = () => {
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

        // Add to followed list IDs
        if (!followedListIds.value.includes(listId)) {
          followedListIds.value.push(listId);
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

        // Remove from followed list IDs
        const index = followedListIds.value.indexOf(listId);
        if (index !== -1) {
          followedListIds.value.splice(index, 1);
        }

        // Refresh the sidebar lists
        await smartListsStore.fetchSmartLists();
      } catch (error) {
        console.error("Failed to unfollow list:", error);
      }
    };

    const handleDeleteList = async (listId) => {
      try {
        const userEmail = userStore.userEmail || "dev@example.com";
        await apiClient.deleteSmartList(listId, userEmail);

        // Remove from owned lists (if it's in there)
        const ownedIndex = myOwnedLists.value.findIndex(
          (list) => list.id === listId,
        );
        if (ownedIndex !== -1) {
          myOwnedLists.value.splice(ownedIndex, 1);
        }

        // Remove from followed list IDs
        const followedIndex = followedListIds.value.indexOf(listId);
        if (followedIndex !== -1) {
          followedListIds.value.splice(followedIndex, 1);
        }

        // Remove from all lists
        const allIndex = allLists.value.findIndex((list) => list.id === listId);
        if (allIndex !== -1) {
          allLists.value.splice(allIndex, 1);
        }

        // Refresh the sidebar lists
        await smartListsStore.fetchSmartLists();
      } catch (error) {
        console.error("Failed to delete list:", error);
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
      await Promise.all([
        fetchAllLists(),
        fetchMyOwnedLists(),
        fetchFollowedListIds(),
      ]);
    });

    return {
      yourLists,
      followedListIds,
      displayedCommunityLists,
      canShowMoreCommunityLists,
      loadingCommunityLists,
      loadingMyLists,
      loadingMore,
      showMoreCommunityLists,
      handleFollowList,
      handleUnfollowList,
      handleDeleteList,
      showCreateList,
      closePanelAndShowWelcome,
    };
  },
};
</script>
