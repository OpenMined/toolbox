<template>
  <div class="h-full flex flex-col p-4">
    <!-- Omni Brand Section -->
    <div class="mb-6">
      <div
        @click="goToWelcome"
        class="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100 transition-colors"
      >
        <div class="w-8 h-8 flex items-center justify-center">
          <img
            src="../assets/om-icon.svg"
            alt="OpenMined Logo"
            class="w-8 h-8"
          />
        </div>
        <div>
          <p class="text-lg font-bold text-gray-900">Omni</p>
          <p class="text-xs text-gray-600">by OpenMined</p>
        </div>
      </div>
    </div>

    <!-- Data Connections Section -->
    <!-- <div class="mb-6">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-sm font-medium text-gray-900">Data Connections</h3>
        <button
          @click="dataSourcesStore.showAddConnector()"
          class="w-6 h-6 text-gray-400 hover:text-gray-600 flex items-center justify-center transition-colors"
        >
          <span class="text-lg font-light">+</span>
        </button>
      </div>
      <div class="space-y-1">
        <div
          v-for="dataSource in dataSourcesStore.dataSources"
          :key="dataSource.id"
          class="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
          :class="{
            'bg-blue-50 border border-blue-200':
              dataSourcesStore.currentDashboard ===
              dataSourcesStore.getDashboardComponent(dataSource.id),
          }"
          @click="dataSourcesStore.toggleConnection(dataSource.id)"
        >
          <div class="flex items-center space-x-3">
            <div
              class="w-2 h-2 rounded-full"
              :class="{
                'bg-green-500': dataSource.connectionState === 'connected',
                'bg-red-500': dataSource.connectionState === 'error',
                'bg-gray-400': dataSource.connectionState === 'disconnected',
              }"
            ></div>
            <span class="text-sm text-gray-700">{{ dataSource.name }}</span>
          </div>
          <span
            v-if="
              dataSource.dashboardData?.totalTweets ||
              dataSource.dashboardData?.totalPapers ||
              dataSource.dashboardData?.totalMessages
            "
            class="text-xs text-gray-400"
          >
            {{
              dataSource.dashboardData.totalTweets ||
              dataSource.dashboardData.totalPapers ||
              dataSource.dashboardData.totalMessages
            }}
          </span>
        </div>
      </div>
    </div> -->

    <!-- Lists Section -->
    <div class="flex-1">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-sm font-medium text-gray-900">Lists</h3>
        <button
          @click="showAddList()"
          class="w-6 h-6 text-gray-400 hover:text-gray-600 flex items-center justify-center transition-colors"
        >
          <span class="text-lg font-light">+</span>
        </button>
      </div>
      <div class="space-y-1">
        <div
          v-for="list in smartListsStore.smartLists"
          :key="list.id"
          class="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50 transition-colors group"
          :class="{
            'bg-blue-50 border border-blue-200':
              list.id === smartListsStore.currentListId,
          }"
        >
          <div
            class="flex items-center flex-1 cursor-pointer"
            @click="selectList(list.id)"
          >
            <span class="text-sm text-gray-700">{{ list.name }}</span>
          </div>
          <div class="flex items-center gap-1">
            <span class="text-xs text-gray-400">{{ list.itemCount }}</span>
            <button
              @click.stop="unfollowList(list.id)"
              class="p-1 hover:bg-red-100 rounded transition-all duration-200 flex-shrink-0"
              title="Unfollow list"
            >
              <svg
                class="h-4 w-4 text-red-500"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  d="M16,12V4H17V2H7V4H8V12L6,14V16H11.2V22H12.8V16H18V14L16,12Z"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- User Account Section (Bottom) -->
    <div class="mt-4 pt-4 border-t border-gray-200">
      <div class="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
        <img
          :src="getUserAvatarUrl()"
          alt="User Avatar"
          class="w-8 h-8 rounded-full"
        />
        <div>
          <p class="text-sm font-medium text-gray-900">
            {{ userAccount.email }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { useDataSourcesStore } from "../stores/dataSourcesStore";
import { useSmartListsStore } from "../stores/smartListsStore";
import { useNewChatStore } from "../stores/newChatStore";
import { useUserStore } from "../stores/userStore";
import { apiClient } from "../api/client.js";

export default {
  name: "LeftSidebar",
  setup() {
    const dataSourcesStore = useDataSourcesStore();
    const smartListsStore = useSmartListsStore();
    const chatStore = useNewChatStore();
    const userStore = useUserStore();

    // Mock user account data - this would come from an auth store in a real app
    const userAccount = { email: "dev@example.com" };

    const getUserAvatarUrl = () => {
      const username = userAccount.email.split("@")[0];
      return `https://i.pravatar.cc/128?u=${username}`;
    };

    const selectList = async (listId) => {
      // Close dashboard to show middle/right panels
      dataSourcesStore.closeDashboard();
      // Set current list
      await smartListsStore.setCurrentList(listId);
      // Close chat panel by default when opening a list
      chatStore.closeChatPanel();
      // Update chat conversations for the selected list
      await chatStore.updateConversationsForList(listId);
    };

    const showAddList = () => {
      dataSourcesStore.setDashboardView("DiscoverListsPanel");
    };

    const unfollowList = async (listId) => {
      try {
        const userEmail = userStore.userEmail || "dev@example.com";
        await apiClient.unfollowSmartList(listId, userEmail);

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

    const goToWelcome = () => {
      // Close any open dashboard
      dataSourcesStore.closeDashboard();
      // Clear current list to show welcome page
      smartListsStore.currentListId = null;
    };

    return {
      dataSourcesStore,
      smartListsStore,
      chatStore,
      userAccount,
      getUserAvatarUrl,
      selectList,
      showAddList,
      unfollowList,
      goToWelcome,
    };
  },
};
</script>
