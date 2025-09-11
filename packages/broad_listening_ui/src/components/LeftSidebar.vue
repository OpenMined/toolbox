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
    <div class="mb-6">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-sm font-medium text-gray-900">Data Connections</h3>
        <button
          @click="connectionsStore.showAddConnector()"
          class="w-6 h-6 text-gray-400 hover:text-gray-600 flex items-center justify-center transition-colors"
        >
          <span class="text-lg font-light">+</span>
        </button>
      </div>
      <div class="space-y-1">
        <div
          v-for="connection in connectionsStore.connections"
          :key="connection.id"
          class="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
          :class="{ 'bg-blue-50 border border-blue-200': connection.isActive }"
          @click="connectionsStore.toggleConnection(connection.id)"
        >
          <div class="flex items-center space-x-3">
            <div class="w-2 h-2 bg-blue-500 rounded-full"></div>
            <span class="text-sm text-gray-700">{{ connection.name }}</span>
          </div>
          <span v-if="connection.tweetCount" class="text-xs text-gray-400">{{
            connection.tweetCount
          }}</span>
        </div>
      </div>
    </div>

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
          v-for="list in listsStore.lists"
          :key="list.id"
          class="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
          :class="{
            'bg-blue-50 border border-blue-200':
              list.id === listsStore.currentListId,
          }"
          @click="selectList(list.id)"
        >
          <span class="text-sm text-gray-700">{{ list.name }}</span>
          <span class="text-xs text-gray-400">{{ list.itemCount }}</span>
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
            {{ connectionsStore.userAccount.email }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { useConnectionsStore } from "../stores/connectionsStore";
import { useListsStore } from "../stores/listsStore";
import { useChatStore } from "../stores/chatStore";

export default {
  name: "LeftSidebar",
  setup() {
    const connectionsStore = useConnectionsStore();
    const listsStore = useListsStore();
    const chatStore = useChatStore();

    const getUserAvatarUrl = () => {
      const username = connectionsStore.userAccount.email.split("@")[0];
      return `https://i.pravatar.cc/128?u=${username}`;
    };

    const selectList = (listId) => {
      // Close dashboard to show middle/right panels
      connectionsStore.closeDashboard();
      // Set current list
      listsStore.setCurrentList(listId);
      // Close chat panel by default when opening a list
      chatStore.closeChatPanel();
      // Update chat conversations for the selected list
      chatStore.updateConversationsForList(listId);
    };

    const showAddList = () => {
      connectionsStore.setDashboardView("CreateList");
    };

    const goToWelcome = () => {
      // Close any open dashboard
      connectionsStore.closeDashboard();
      // Clear current list to show welcome page
      listsStore.currentListId = null;
    };

    return {
      connectionsStore,
      listsStore,
      chatStore,
      getUserAvatarUrl,
      selectList,
      showAddList,
      goToWelcome,
    };
  },
};
</script>
