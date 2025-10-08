<template>
  <div class="h-full bg-white overflow-y-auto">
    <div class="max-w-4xl mx-auto py-16 px-8">
      <!-- Welcome Header -->
      <div class="text-center mb-20">
        <div class="w-16 h-16 mx-auto mb-8">
          <img src="../assets/om-icon.svg" alt="Omni Logo" class="w-16 h-16" />
        </div>
        <h1 class="text-4xl font-light text-gray-900 mb-4">Welcome to Omni</h1>
        <p class="text-lg text-gray-600 font-light">
          Follow topics from multiple platforms
        </p>
      </div>

      <!-- Overview Sections -->
      <div class="space-y-20">
        <!-- Lists Overview -->
        <div>
          <div class="mb-8">
            <h2 class="text-2xl font-light text-gray-900">Your Lists</h2>
          </div>

          <!-- Your Lists (owned + followed community lists) -->
          <div v-if="yourLists.length > 0" class="max-w-2xl">
            <SmartListListView
              :lists="yourLists"
              :show-owned-lists="true"
              :show-delete-button="true"
              :show-your-lists="true"
              :followed-list-ids="followedListIds"
              :clickable="true"
              @follow="followAndOpenList"
              @unfollow="unfollowList"
              @delete="deleteList"
              @click="openList"
            />
          </div>

          <!-- Empty State for Your Lists -->
          <div
            v-else
            class="text-center py-4 bg-gray-50 rounded-lg border border-gray-200"
          >
            <p class="text-gray-600 text-sm">
              You haven't created any lists yet
            </p>
          </div>
        </div>

        <!-- Available Lists to Explore -->
        <div v-if="communityLists.length > 0">
          <div class="mb-8">
            <h2 class="text-2xl font-light text-gray-900">Community Lists</h2>
            <p class="text-gray-600 mt-2">
              Discover and follow existing smart lists
            </p>
          </div>

          <div class="max-w-2xl">
            <SmartListListView
              :lists="communityLists"
              :show-follow-button="true"
              @follow="followAndOpenList"
            />
          </div>

          <div class="flex flex-col sm:flex-row gap-3 justify-center pt-6">
            <button
              @click="discoverLists"
              class="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
            >
              Discover All Lists
            </button>
            <button
              @click="createNewList"
              class="inline-flex items-center px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
            >
              Create Your Own
            </button>
          </div>
        </div>

        <!-- Fallback if no lists exist at all -->
        <div
          v-if="allLists.length === 0"
          class="text-center py-16 bg-gray-50 rounded-lg border-2 border-dashed border-gray-200"
        >
          <div
            class="w-16 h-16 mx-auto mb-6 bg-blue-50 rounded-full flex items-center justify-center"
          >
            <svg
              class="w-8 h-8 text-blue-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
              ></path>
            </svg>
          </div>
          <h3 class="text-lg font-medium text-gray-900 mb-2">
            No smart lists available
          </h3>
          <p class="text-gray-600 mb-6 max-w-sm mx-auto">
            Be the first to create a smart list
          </p>
          <button
            @click="createNewList"
            class="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
          >
            Create Your First List
          </button>
        </div>

        <!-- Data Sources Overview -->
        <!-- <div>
          <div class="flex items-center justify-between mb-8">
            <h2 class="text-2xl font-light text-gray-900">Data Sources</h2>
            <button
              @click="manageConnectors"
              class="text-blue-600 hover:text-blue-700 font-medium transition-colors"
            >
              Manage connectors
            </button>
          </div>

          <div
            v-if="connectedSources.length > 0"
            class="grid gap-6 md:grid-cols-2 lg:grid-cols-3"
          >
            <div
              v-for="source in connectedSources"
              :key="source.id"
              class="p-6 border border-gray-100 rounded-lg"
            >
              <div class="flex items-center space-x-3 mb-3">
                <div
                  class="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center"
                >
                  <div
                    class="w-6 h-6 rounded"
                    :class="{
                      'bg-blue-500': source.id === 'twitter',
                      'bg-indigo-500': source.id === 'discord',
                      'bg-purple-500': source.id === 'ai-papers',
                    }"
                  ></div>
                </div>
                <div>
                  <h3 class="font-medium text-gray-900">{{ source.name }}</h3>
                  <div class="flex items-center space-x-1">
                    <div
                      class="w-2 h-2 rounded-full"
                      :class="{
                        'bg-green-500': source.connectionState === 'connected',
                        'bg-red-500': source.connectionState === 'error',
                        'bg-gray-400':
                          source.connectionState === 'disconnected',
                      }"
                    ></div>
                    <span class="text-sm text-gray-600">{{
                      source.connectionState
                    }}</span>
                  </div>
                </div>
              </div>
              <p
                v-if="source.dashboardData?.totalTweets"
                class="text-sm text-gray-600"
              >
                {{ source.dashboardData.totalTweets }} tweets
              </p>
              <p
                v-if="source.dashboardData?.totalMessages"
                class="text-sm text-gray-600"
              >
                {{ source.dashboardData.totalMessages }} messages
              </p>
              <p
                v-if="source.dashboardData?.totalPapers"
                class="text-sm text-gray-600"
              >
                {{ source.dashboardData.totalPapers }} papers
              </p>
            </div>
          </div>

          <div v-else class="text-center py-12">
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
                  d="M7 21l3-3 3 3 7-7v3m0 0v3m0-3h3M1 5h12m0 0l4-4m4 4H9m8 0l4-4"
                ></path>
              </svg>
            </div>
            <p class="text-gray-600 mb-4">No data sources connected</p>
            <button
              @click="manageConnectors"
              class="text-blue-600 hover:text-blue-700 font-medium"
            >
              Connect your first data source
            </button>
          </div>
        </div> -->

        <!-- Getting Started -->
        <!-- <div class="border-t border-gray-100 pt-20">
          <h2 class="text-2xl font-light text-gray-900 mb-8 text-center">
            Getting Started
          </h2>
          <div class="grid gap-8 md:grid-cols-2 max-w-2xl mx-auto">
            <div class="text-center">
              <div
                class="w-12 h-12 mx-auto mb-4 bg-blue-100 rounded-full flex items-center justify-center"
              >
                <span class="text-lg font-medium text-blue-600">1</span>
              </div>
              <h3 class="font-medium text-gray-900 mb-2">
                Connect Data Sources
              </h3>
              <p class="text-sm text-gray-600">
                Link your Twitter, Discord, and AI paper feeds
              </p>
            </div>
            <div class="text-center">
              <div
                class="w-12 h-12 mx-auto mb-4 bg-blue-100 rounded-full flex items-center justify-center"
              >
                <span class="text-lg font-medium text-blue-600">1</span>
              </div>
              <h3 class="font-medium text-gray-900 mb-2">Follow existing Smart lists or Create your own</h3>
              <p class="text-sm text-gray-600">
                Organize content with custom filters and criteria
              </p>
            </div>
            <div class="text-center">
              <div
                class="w-12 h-12 mx-auto mb-4 bg-blue-100 rounded-full flex items-center justify-center"
              >
                <span class="text-lg font-medium text-blue-600">2</span>
              </div>
              <h3 class="font-medium text-gray-900 mb-2">Explore & Chat</h3>
              <p class="text-sm text-gray-600">
                Browse your curated content and ask questions
              </p>
            </div>
          </div>
        </div> -->
      </div>
    </div>
  </div>
</template>

<script>
import { computed, ref, onMounted, watch } from "vue";
import { useDataSourcesStore } from "../stores/dataSourcesStore";
import { useSmartListsStore } from "../stores/smartListsStore";
import { useNewChatStore } from "../stores/newChatStore";
import { useUserStore } from "../stores/userStore";
import { apiClient } from "../api/client.js";
import SmartListListView from "./SmartListListView.vue";

export default {
  name: "WelcomePage",
  components: {
    SmartListListView,
  },
  setup() {
    const dataSourcesStore = useDataSourcesStore();
    const smartListsStore = useSmartListsStore();
    const chatStore = useNewChatStore();
    const userStore = useUserStore();

    const allLists = ref([]);
    const myOwnedLists = ref([]);
    const followedListIds = ref([]);

    // Get connected data sources
    const connectedSources = computed(() => {
      return dataSourcesStore.connectedDataSources;
    });

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
    });

    // Get community lists (unfollowed lists not created by current user)
    const communityLists = computed(() => {
      const currentUserEmail = userStore.userEmail || "dev@example.com";

      return allLists.value.filter(
        (list) =>
          list.owner_email !== currentUserEmail &&
          !followedListIds.value.includes(list.id),
      );
    });

    const fetchAllLists = async () => {
      try {
        const userEmail = userStore.userEmail || "dev@example.com";
        allLists.value = await apiClient.getSmartLists(userEmail);
      } catch (error) {
        console.error("Failed to fetch all lists:", error);
      }
    };

    const fetchMyOwnedLists = async () => {
      try {
        const userEmail = userStore.userEmail || "dev@example.com";
        const lists = await apiClient.getMySmartLists(userEmail);
        myOwnedLists.value = lists;
      } catch (error) {
        console.error("Failed to fetch my owned lists:", error);
      }
    };

    const fetchFollowedListIds = async () => {
      try {
        const userEmail = userStore.userEmail || "dev@example.com";
        const followedLists = await apiClient.getFollowedSmartLists(userEmail);
        followedListIds.value = followedLists.map((list) => list.id);
      } catch (error) {
        console.error("Failed to fetch followed list IDs:", error);
      }
    };

    const followAndOpenList = async (listId) => {
      try {
        const userEmail = userStore.userEmail || "dev@example.com";
        await apiClient.followSmartList(listId, userEmail);

        // Add to followed list IDs
        if (!followedListIds.value.includes(listId)) {
          followedListIds.value.push(listId);
        }

        // Refresh the sidebar lists
        await smartListsStore.fetchSmartLists();

        // Open the list
        dataSourcesStore.closeDashboard();
        await smartListsStore.setCurrentList(listId);
        chatStore.closeChatPanel();
        await chatStore.updateConversationsForList(listId);
      } catch (error) {
        console.error("Failed to follow and open list:", error);
      }
    };

    const unfollowList = async (listId) => {
      try {
        const userEmail = userStore.userEmail || "dev@example.com";
        await apiClient.unfollowSmartList(listId, userEmail);

        // Remove from followed list IDs
        const index = followedListIds.value.indexOf(listId);
        if (index !== -1) {
          followedListIds.value.splice(index, 1);
        }

        // If we're currently viewing the unfollowed list, go to welcome page
        if (smartListsStore.currentListId === listId) {
          smartListsStore.currentListId = null;
          dataSourcesStore.closeDashboard();
        }

        // Refresh the sidebar lists
        await smartListsStore.fetchSmartLists();
      } catch (error) {
        console.error("Failed to unfollow list:", error);
      }
    };

    const deleteList = async (listId) => {
      try {
        const userEmail = userStore.userEmail || "dev@example.com";
        await apiClient.deleteSmartList(listId, userEmail);

        // Remove from owned lists
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

        // If we're currently viewing the deleted list, go to welcome page
        if (smartListsStore.currentListId === listId) {
          smartListsStore.currentListId = null;
          dataSourcesStore.closeDashboard();
        }

        // Refresh the sidebar lists
        await smartListsStore.fetchSmartLists();
      } catch (error) {
        console.error("Failed to delete list:", error);
      }
    };

    const createNewList = () => {
      dataSourcesStore.setDashboardView("CreateList");
    };

    const discoverLists = () => {
      dataSourcesStore.setDashboardView("DiscoverListsPanel");
    };

    const manageConnectors = () => {
      dataSourcesStore.setDashboardView("ConnectorManager");
    };

    const openList = async (listId) => {
      dataSourcesStore.closeDashboard();
      await smartListsStore.setCurrentList(listId);
      chatStore.closeChatPanel(); // Start with chat panel closed
      await chatStore.updateConversationsForList(listId);
    };

    const refreshData = async () => {
      await Promise.all([
        fetchAllLists(),
        fetchMyOwnedLists(),
        fetchFollowedListIds(),
      ]);
    };

    onMounted(async () => {
      // Fetch all lists, owned lists, and followed list IDs when component mounts
      // This will run every time the component is shown (including after creating a list)
      await refreshData();
    });

    return {
      dataSourcesStore,
      smartListsStore,
      connectedSources,
      allLists,
      myOwnedLists,
      yourLists,
      followedListIds,
      communityLists,
      createNewList,
      discoverLists,
      manageConnectors,
      openList,
      followAndOpenList,
      unfollowList,
      deleteList,
    };
  },
};
</script>
