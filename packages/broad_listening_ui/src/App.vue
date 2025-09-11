<template>
  <div class="flex h-screen bg-gray-50">
    <!-- Left Sidebar -->
    <div class="w-64 bg-white border-r border-gray-200">
      <LeftSidebar />
    </div>

    <!-- Main Content Area -->
    <div class="flex-1 flex" v-if="!connectionsStore.showDashboard">
      <!-- Welcome Page (default) -->
      <div v-if="!listsStore.currentListId" class="flex-1">
        <WelcomePage />
      </div>

      <!-- List View -->
      <div v-else class="flex-1 flex">
        <!-- Middle Panel -->
        <div
          class="flex flex-col"
          :class="chatStore.isChatPanelOpen ? 'flex-1' : 'flex-1'"
        >
          <MiddlePanel />
        </div>

        <!-- Right Panel (Chat) - Only show when chat panel is open -->
        <div
          v-if="chatStore.isChatPanelOpen"
          class="flex-1 bg-white border-l border-gray-200"
          :class="{ highlighted: chatStore.isHighlighted }"
        >
          <RightPanel />
        </div>
      </div>
    </div>

    <!-- Dashboard View -->
    <div class="flex-1 flex flex-col" v-else>
      <component :is="connectionsStore.currentDashboard" />
    </div>
  </div>
</template>

<script>
import { onMounted } from "vue";
import { useChatStore } from "./stores/chatStore";
import { useConnectionsStore } from "./stores/connectionsStore";
import { useListsStore } from "./stores/listsStore";
import LeftSidebar from "./components/LeftSidebar.vue";
import MiddlePanel from "./components/MiddlePanel.vue";
import RightPanel from "./components/RightPanel.vue";
import TwitterDashboard from "./components/TwitterDashboard.vue";
import AIPapersDashboard from "./components/AIPapersDashboard.vue";
import DiscordDashboard from "./components/DiscordDashboard.vue";
import AddConnector from "./components/AddConnector.vue";
import AddList from "./components/AddList.vue";
import CreateList from "./components/CreateList.vue";
import ConnectorManager from "./components/ConnectorManager.vue";
import WelcomePage from "./components/WelcomePage.vue";

export default {
  name: "App",
  components: {
    LeftSidebar,
    MiddlePanel,
    RightPanel,
    TwitterDashboard,
    AIPapersDashboard,
    DiscordDashboard,
    AddConnector,
    AddList,
    CreateList,
    ConnectorManager,
    WelcomePage,
  },
  setup() {
    const chatStore = useChatStore();
    const connectionsStore = useConnectionsStore();
    const listsStore = useListsStore();

    onMounted(() => {
      chatStore.initializeDefaultConversations();
      // Start with no list selected to show welcome page
      listsStore.currentListId = null;
    });

    return {
      chatStore,
      connectionsStore,
      listsStore,
    };
  },
};
</script>
