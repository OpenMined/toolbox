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
          Broad listening to the web and your private data
        </p>
      </div>

      <!-- Overview Sections -->
      <div class="space-y-20">
        <!-- Lists Overview -->
        <div>
          <div class="flex items-center justify-between mb-8">
            <h2 class="text-2xl font-light text-gray-900">Your Lists</h2>
            <button
              @click="createNewList"
              class="text-blue-600 hover:text-blue-700 font-medium transition-colors"
            >
              Create list
            </button>
          </div>

          <div
            v-if="listsStore.lists.length > 0"
            class="grid gap-6 md:grid-cols-2 lg:grid-cols-3"
          >
            <div
              v-for="list in listsStore.lists"
              :key="list.id"
              @click="openList(list.id)"
              class="p-6 border border-gray-100 rounded-lg hover:bg-gray-50 cursor-pointer transition-all duration-200"
            >
              <h3 class="font-medium text-gray-900 mb-2">{{ list.name }}</h3>
              <p class="text-sm text-gray-600">{{ list.itemCount }} items</p>
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
                  d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                ></path>
              </svg>
            </div>
            <p class="text-gray-600 mb-4">No lists created yet</p>
            <button
              @click="createNewList"
              class="text-blue-600 hover:text-blue-700 font-medium"
            >
              Create your first list
            </button>
          </div>
        </div>

        <!-- Data Sources Overview -->
        <div>
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
                      'bg-blue-500': source.type === 'twitter',
                      'bg-indigo-500': source.type === 'discord',
                      'bg-purple-500': source.type === 'ai-papers',
                    }"
                  ></div>
                </div>
                <div>
                  <h3 class="font-medium text-gray-900">{{ source.name }}</h3>
                  <div class="flex items-center space-x-1">
                    <div class="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span class="text-sm text-gray-600">Connected</span>
                  </div>
                </div>
              </div>
              <p v-if="source.tweetCount" class="text-sm text-gray-600">
                {{ source.tweetCount }} tweets
              </p>
              <p v-if="source.messageCount" class="text-sm text-gray-600">
                {{ source.messageCount }} messages
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
        </div>

        <!-- Getting Started -->
        <div class="border-t border-gray-100 pt-20">
          <h2 class="text-2xl font-light text-gray-900 mb-8 text-center">
            Getting Started
          </h2>
          <div class="grid gap-8 md:grid-cols-3">
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
                <span class="text-lg font-medium text-blue-600">2</span>
              </div>
              <h3 class="font-medium text-gray-900 mb-2">Create Lists</h3>
              <p class="text-sm text-gray-600">
                Organize content with custom filters and criteria
              </p>
            </div>
            <div class="text-center">
              <div
                class="w-12 h-12 mx-auto mb-4 bg-blue-100 rounded-full flex items-center justify-center"
              >
                <span class="text-lg font-medium text-blue-600">3</span>
              </div>
              <h3 class="font-medium text-gray-900 mb-2">Explore & Chat</h3>
              <p class="text-sm text-gray-600">
                Browse your curated content and ask questions
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from "vue";
import { useConnectionsStore } from "../stores/connectionsStore";
import { useListsStore } from "../stores/listsStore";
import { useChatStore } from "../stores/chatStore";

export default {
  name: "WelcomePage",
  setup() {
    const connectionsStore = useConnectionsStore();
    const listsStore = useListsStore();
    const chatStore = useChatStore();

    // Get connected data sources
    const connectedSources = computed(() => {
      return connectionsStore.connections.filter(
        (connection) => connection.isActive,
      );
    });

    const createNewList = () => {
      connectionsStore.setDashboardView("CreateList");
    };

    const manageConnectors = () => {
      connectionsStore.setDashboardView("ConnectorManager");
    };

    const openList = (listId) => {
      connectionsStore.closeDashboard();
      listsStore.setCurrentList(listId);
      chatStore.closeChatPanel(); // Start with chat panel closed
      chatStore.updateConversationsForList(listId);
    };

    return {
      connectionsStore,
      listsStore,
      connectedSources,
      createNewList,
      manageConnectors,
      openList,
    };
  },
};
</script>
