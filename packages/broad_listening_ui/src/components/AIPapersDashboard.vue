<template>
  <div class="h-full bg-white">
    <!-- Dashboard Header -->
    <div class="p-6 border-b border-gray-200">
      <div class="flex items-center justify-between">
        <h2 class="text-2xl font-bold text-gray-900">AI Papers Dashboard</h2>
        <button
          @click="connectionsStore.closeDashboard()"
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

    <div class="p-6">
      <!-- Stats Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <!-- Source: Trending Papers -->
        <div class="bg-orange-50 rounded-lg p-4">
          <div class="flex items-center">
            <div
              class="p-2 bg-orange-500 rounded-lg flex items-center justify-center"
            >
              <!-- HuggingFace logo placeholder -->
              <svg
                class="w-6 h-6 text-white"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"
                />
              </svg>
            </div>
            <div class="ml-4">
              <p class="text-sm font-medium text-gray-600">
                Source: Trending Papers
              </p>
              <p class="text-lg font-bold text-gray-900">
                {{ dashboardData.trendingPapers }}
              </p>
            </div>
          </div>
        </div>

        <!-- Papers from SyftBox Network -->
        <div class="bg-purple-50 rounded-lg p-4">
          <div class="flex items-center">
            <div
              class="p-2 bg-purple-500 rounded-lg flex items-center justify-center"
            >
              <img src="../assets/om-icon.svg" alt="SyftBox" class="w-6 h-6" />
            </div>
            <div class="ml-4">
              <p class="text-sm font-medium text-gray-600">
                Papers from SyftBox Network
              </p>
              <p class="text-lg font-bold text-gray-900">
                {{ dashboardData.syftboxPapers }}
              </p>
            </div>
          </div>
        </div>

        <!-- Latest Paper -->
        <div class="bg-green-50 rounded-lg p-4">
          <div class="flex items-center">
            <div class="p-2 bg-green-500 rounded-lg">
              <svg
                class="w-6 h-6 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                ></path>
              </svg>
            </div>
            <div class="ml-4">
              <p class="text-sm font-medium text-gray-600">Latest Paper</p>
              <div class="flex items-center space-x-2">
                <p class="text-lg font-bold text-gray-900">
                  {{ dashboardData.latestPaper }}
                </p>
                <svg
                  class="w-4 h-4 text-black"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fill-rule="evenodd"
                    d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z"
                    clip-rule="evenodd"
                  ></path>
                </svg>
              </div>
            </div>
          </div>
        </div>

        <!-- Total Papers -->
        <div class="bg-blue-50 rounded-lg p-4">
          <div class="flex items-center">
            <div class="p-2 bg-blue-500 rounded-lg">
              <svg
                class="w-6 h-6 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                ></path>
              </svg>
            </div>
            <div class="ml-4">
              <p class="text-sm font-medium text-gray-600">Total Papers</p>
              <p class="text-lg font-bold text-gray-900">
                {{ dashboardData.totalPapers }}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <!-- Latest Papers -->
        <div class="bg-white rounded-lg border border-gray-200 p-6">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">
            Latest Papers
          </h3>
          <div class="space-y-4">
            <div
              v-for="paper in dashboardData.latestPapers"
              :key="paper.id"
              class="p-4 border border-gray-100 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <h4 class="text-sm font-semibold text-gray-900 mb-2">
                {{ paper.title }}
              </h4>
              <p class="text-xs text-gray-600 mb-2">
                {{ paper.authors }} • {{ paper.arxivId }}
              </p>
              <p class="text-sm text-gray-700 mb-2">{{ paper.summary }}</p>
              <div
                class="flex items-center justify-between text-xs text-gray-500"
              >
                <span>{{ paper.timestamp }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Papers with Embeddings -->
        <div class="bg-white rounded-lg border border-gray-200 p-6">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">
            Papers with Embeddings
          </h3>
          <div class="space-y-4">
            <div
              v-for="(count, model) in dashboardData.embeddingCounts"
              :key="model"
              class="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <div class="flex items-center">
                <div
                  class="w-3 h-3 rounded-full mr-3"
                  :class="{
                    'bg-blue-500': model === 'ollama/nomic-embed-text',
                    'bg-green-500': model === 'openai/text-embedding-3-small',
                  }"
                ></div>
                <span
                  class="text-sm font-mono font-medium text-gray-900 bg-gray-200 px-2 py-1 rounded"
                  >{{ model }}</span
                >
              </div>
              <div class="flex items-center">
                <span class="text-sm font-semibold text-gray-700 mr-3">{{
                  count
                }}</span>
                <div class="w-16 bg-gray-200 rounded-full h-2">
                  <div
                    class="h-2 rounded-full"
                    :class="{
                      'bg-blue-500': model === 'ollama/nomic-embed-text',
                      'bg-green-500': model === 'openai/text-embedding-3-small',
                    }"
                    :style="`width: ${
                      (count /
                        Math.max(
                          ...Object.values(dashboardData.embeddingCounts),
                        )) *
                      100
                    }%`"
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { useConnectionsStore } from "../stores/connectionsStore";

export default {
  name: "AIPapersDashboard",
  setup() {
    const connectionsStore = useConnectionsStore();

    return {
      connectionsStore,
      dashboardData: connectionsStore.dashboardData.aiPapers,
    };
  },
};
</script>
