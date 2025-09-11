<template>
  <div class="h-full bg-white">
    <!-- Dashboard Header -->
    <div class="p-6 border-b border-gray-200">
      <div class="flex items-center justify-between">
        <h2 class="text-2xl font-bold text-gray-900">Twitter Dashboard</h2>
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
        <!-- Twitter Handle -->
        <div class="bg-blue-50 rounded-lg p-4">
          <div class="flex items-center">
            <div class="p-2 bg-blue-500 rounded-lg">
              <svg
                class="w-6 h-6 text-white"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"
                />
              </svg>
            </div>
            <div class="ml-4">
              <p class="text-sm font-medium text-gray-600">Your Handle</p>
              <p class="text-lg font-bold text-gray-900">
                {{ dashboardData.handle }}
              </p>
            </div>
          </div>
        </div>

        <!-- Total Tweets -->
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
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                ></path>
              </svg>
            </div>
            <div class="ml-4">
              <p class="text-sm font-medium text-gray-600">Total Tweets</p>
              <p class="text-lg font-bold text-gray-900">
                {{ dashboardData.totalTweets }}
              </p>
            </div>
          </div>
        </div>

        <!-- SyftBox Tweets -->
        <div class="bg-purple-50 rounded-lg p-4">
          <div class="flex items-center">
            <div
              class="p-2 bg-purple-500 rounded-lg flex items-center justify-center"
            >
              <img src="../assets/om-icon.svg" alt="SyftBox" class="w-6 h-6" />
            </div>
            <div class="ml-4">
              <p class="text-sm font-medium text-gray-600">
                Tweets from SyftBox Network
              </p>
              <p class="text-lg font-bold text-gray-900">
                {{ dashboardData.syftboxTweets }}
              </p>
            </div>
          </div>
        </div>

        <!-- Latest Tweet Date -->
        <div class="bg-orange-50 rounded-lg p-4">
          <div class="flex items-center">
            <div class="p-2 bg-orange-500 rounded-lg">
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
              <p class="text-sm font-medium text-gray-600">Latest Tweet</p>
              <div class="flex items-center space-x-2">
                <p class="text-lg font-bold text-gray-900">
                  {{ dashboardData.latestTweetDate }}
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
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <!-- Latest Tweets -->
        <div class="bg-white rounded-lg border border-gray-200 p-6">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">
            Latest Tweets
          </h3>
          <div class="space-y-4">
            <div
              v-for="tweet in dashboardData.latestTweets"
              :key="tweet.id"
              class="p-4 border border-gray-100 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <p class="text-sm text-gray-700 mb-2">{{ tweet.content }}</p>
              <div
                class="flex items-center justify-between text-xs text-gray-500"
              >
                <span>{{ tweet.timestamp }}</span>
                <div class="flex items-center space-x-4">
                  <span class="flex items-center">
                    <svg
                      class="w-4 h-4 mr-1"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fill-rule="evenodd"
                        d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z"
                        clip-rule="evenodd"
                      ></path>
                    </svg>
                    {{ tweet.likes }}
                  </span>
                  <span class="flex items-center">
                    <svg
                      class="w-4 h-4 mr-1"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        d="M15 8a3 3 0 10-2.977-2.63l-4.94 2.47a3 3 0 100 4.319l4.94 2.47a3 3 0 10.895-1.789l-4.94-2.47a3.027 3.027 0 000-.74l4.94-2.47C13.456 7.68 14.19 8 15 8z"
                      ></path>
                    </svg>
                    {{ tweet.retweets }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Embeddings by AI Model -->
        <div class="bg-white rounded-lg border border-gray-200 p-6">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">
            Tweets with Embeddings
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
  name: "TwitterDashboard",
  setup() {
    const connectionsStore = useConnectionsStore();

    return {
      connectionsStore,
      dashboardData: connectionsStore.dashboardData.twitter,
    };
  },
};
</script>
