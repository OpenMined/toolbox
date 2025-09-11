<template>
  <div class="flex h-screen bg-gray-50">
    <!-- Left Sidebar -->
    <div class="w-64 bg-white border-r border-gray-200">
      <LeftSidebar />
    </div>

    <!-- Main Content Area -->
    <div class="flex-1 flex" v-if="!connectionsStore.showDashboard">
      <!-- Middle Panel -->
      <div class="flex-1 flex flex-col">
        <MiddlePanel />
      </div>

      <!-- Right Panel -->
      <div
        class="flex-1 bg-white border-l border-gray-200"
        :class="{ highlighted: chatStore.isHighlighted }"
      >
        <RightPanel />
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
import LeftSidebar from "./components/LeftSidebar.vue";
import MiddlePanel from "./components/MiddlePanel.vue";
import RightPanel from "./components/RightPanel.vue";
import TwitterDashboard from "./components/TwitterDashboard.vue";
import AIPapersDashboard from "./components/AIPapersDashboard.vue";
import AddConnector from "./components/AddConnector.vue";
import AddList from "./components/AddList.vue";

export default {
  name: "App",
  components: {
    LeftSidebar,
    MiddlePanel,
    RightPanel,
    TwitterDashboard,
    AIPapersDashboard,
    AddConnector,
    AddList,
  },
  setup() {
    const chatStore = useChatStore();
    const connectionsStore = useConnectionsStore();

    onMounted(() => {
      chatStore.initializeDefaultConversations();
    });

    return {
      chatStore,
      connectionsStore,
    };
  },
};
</script>
