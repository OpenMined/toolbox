<template>
  <div class="h-full bg-white flex">
    <!-- Header -->
    <div
      class="absolute top-0 left-0 right-0 p-6 border-b border-gray-200 bg-white z-10"
    >
      <div class="flex items-center justify-between">
        <h2 class="text-2xl font-bold text-gray-900">Data Connectors</h2>
        <button
          @click="dataSourcesStore.closeDashboard()"
          class="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full"
        >
          <svg
            class="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M6 18L18 6M6 6l12 12"
            ></path>
          </svg>
        </button>
      </div>
    </div>

    <!-- Left Sidebar - Data Sources -->
    <div class="w-80 border-r border-gray-200 pt-20">
      <div class="p-6">
        <h3 class="text-sm font-medium text-gray-900 mb-4">
          Available Sources
        </h3>
        <div class="space-y-2">
          <div
            v-for="source in dataSources"
            :key="source.id"
            @click="selectSource(source)"
            class="flex items-center space-x-3 p-3 rounded-lg cursor-pointer transition-colors"
            :class="{
              'bg-blue-50 border border-blue-200':
                selectedSource?.id === source.id,
              'hover:bg-gray-50': selectedSource?.id !== source.id,
            }"
          >
            <div class="relative">
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
              <!-- Connection Status Dot -->
              <div
                class="absolute -top-1 -right-1 w-4 h-4 rounded-full border-2 border-white"
                :class="{
                  'bg-green-500': connectedSources.includes(source.id),
                  'bg-gray-300': !connectedSources.includes(source.id),
                }"
              ></div>
            </div>
            <div class="flex-1">
              <p class="font-medium text-gray-900">{{ source.name }}</p>
              <p class="text-sm text-gray-500">
                {{
                  connectedSources.includes(source.id)
                    ? "Connected"
                    : "Not connected"
                }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content - Onboarding -->
    <div class="flex-1 pt-20">
      <div class="h-full overflow-y-auto">
        <div
          v-if="!selectedSource"
          class="flex items-center justify-center h-full"
        >
          <div class="text-center text-gray-500">
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
            <p class="text-lg">Select a data source to get started</p>
            <p class="text-sm mt-2">
              Choose from the available sources on the left to begin setup
            </p>
          </div>
        </div>

        <div v-else class="max-w-2xl mx-auto p-8">
          <!-- Onboarding Flow -->
          <div class="space-y-8">
            <!-- Header -->
            <div class="text-center">
              <div
                class="w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center"
                :class="{
                  'bg-blue-100': selectedSource.id === 'twitter',
                  'bg-indigo-100': selectedSource.id === 'discord',
                  'bg-purple-100': selectedSource.id === 'ai-papers',
                }"
              >
                <div
                  class="w-8 h-8 rounded"
                  :class="{
                    'bg-blue-600': selectedSource.id === 'twitter',
                    'bg-indigo-600': selectedSource.id === 'discord',
                    'bg-purple-600': selectedSource.id === 'ai-papers',
                  }"
                ></div>
              </div>
              <h3 class="text-2xl font-semibold text-gray-900 mb-4">
                Connect {{ selectedSource.name }}
              </h3>
              <p class="text-gray-600">{{ selectedSource.description }}</p>
            </div>

            <!-- Prerequisites -->
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <div class="flex items-start space-x-3">
                <div
                  class="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"
                >
                  <span class="text-white text-sm font-semibold">!</span>
                </div>
                <div>
                  <h4 class="font-semibold text-gray-900 mb-2">
                    Toolbox Required
                  </h4>
                  <p class="text-gray-600 mb-3">
                    This app requires the OpenMined Toolbox to manage data
                    connectors.
                  </p>
                  <a
                    href="https://github.com/OpenMined/toolbox"
                    target="_blank"
                    class="text-blue-600 hover:text-blue-800 underline"
                  >
                    Visit GitHub Repository →
                  </a>
                </div>
              </div>
            </div>

            <!-- Installation -->
            <div class="space-y-4">
              <h4 class="font-semibold text-gray-900">
                Install {{ selectedSource.name }} Connector
              </h4>
              <p class="text-gray-600">
                Run this command to install the {{ selectedSource.name }} MCP
                connector:
              </p>
              <div
                class="relative bg-gray-900 text-gray-100 p-4 rounded-lg font-mono text-sm"
              >
                <div class="pr-12">{{ selectedSource.installCommand }}</div>
                <button
                  @click="copyCommand(selectedSource.installCommand)"
                  class="absolute top-4 right-4 p-1 text-gray-400 hover:text-gray-200 transition-colors"
                  :title="commandCopied ? 'Copied!' : 'Copy command'"
                >
                  <svg
                    v-if="!commandCopied"
                    class="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                    ></path>
                  </svg>
                  <svg
                    v-else
                    class="w-4 h-4 text-green-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M5 13l4 4L19 7"
                    ></path>
                  </svg>
                </button>
              </div>
            </div>

            <!-- Connection -->
            <div class="space-y-4">
              <h4 class="font-semibold text-gray-900">
                Connect to Your {{ selectedSource.name }} MCP
              </h4>
              <p class="text-gray-600">
                Enter the URL of your {{ selectedSource.name }} MCP server:
              </p>
              <div class="space-y-3">
                <input
                  v-model="serverUrl"
                  type="text"
                  class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  :placeholder="selectedSource.defaultUrl"
                />
                <button
                  @click="connect"
                  :disabled="
                    !serverUrl.trim() ||
                    isConnecting ||
                    connectedSources.includes(selectedSource.id)
                  "
                  class="w-full py-3 px-4 rounded-lg font-medium transition-all duration-200"
                  :class="{
                    'bg-green-600 text-white': connectedSources.includes(
                      selectedSource.id,
                    ),
                    'bg-blue-600 text-white hover:bg-blue-700':
                      !isConnecting &&
                      serverUrl.trim() &&
                      !connectedSources.includes(selectedSource.id),
                    'bg-gray-300 text-gray-500 cursor-not-allowed':
                      !serverUrl.trim() || isConnecting,
                  }"
                >
                  <div
                    v-if="connectedSources.includes(selectedSource.id)"
                    class="flex items-center justify-center"
                  >
                    <svg
                      class="w-5 h-5 mr-2"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M5 13l4 4L19 7"
                      ></path>
                    </svg>
                    Connected
                  </div>
                  <div
                    v-else-if="isConnecting"
                    class="flex items-center justify-center"
                  >
                    <svg
                      class="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
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
                    Connecting...
                  </div>
                  <span v-else>Connect</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from "vue";
import { useDataSourcesStore } from "../stores/dataSourcesStore";

export default {
  name: "ConnectorManager",
  setup() {
    const dataSourcesStore = useDataSourcesStore();
    const selectedSource = ref(null);
    const serverUrl = ref("");
    const isConnecting = ref(false);
    const commandCopied = ref(false);

    // Get data sources from store
    const dataSources = computed(() => dataSourcesStore.dataSources);

    // Get connected sources from store
    const connectedSources = computed(() =>
      dataSourcesStore.dataSources
        .filter((ds) => ds.connectionState === "connected")
        .map((ds) => ds.id),
    );

    const selectSource = (source) => {
      selectedSource.value = source;
      serverUrl.value = source.defaultUrl;
    };

    const copyCommand = async (command) => {
      try {
        await navigator.clipboard.writeText(command);
        commandCopied.value = true;
        setTimeout(() => {
          commandCopied.value = false;
        }, 2000);
      } catch (err) {
        console.error("Failed to copy command:", err);
      }
    };

    const connect = async () => {
      if (!selectedSource.value || !serverUrl.value.trim()) return;

      isConnecting.value = true;

      // Simulate connection process
      setTimeout(() => {
        // Update the data source connection state in the store
        dataSourcesStore.updateConnectionState(
          selectedSource.value.id,
          "connected",
        );
        isConnecting.value = false;
      }, 1000);
    };

    return {
      dataSourcesStore,
      dataSources,
      selectedSource,
      serverUrl,
      connectedSources,
      isConnecting,
      commandCopied,
      selectSource,
      copyCommand,
      connect,
    };
  },
};
</script>
