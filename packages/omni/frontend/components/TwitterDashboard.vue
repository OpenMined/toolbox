<template>
  <div class="h-full bg-gray-50 overflow-y-auto">
    <!-- Header -->
    <div class="bg-white border-b border-gray-200 px-6 py-4">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">Twitter Dashboard</h1>
          <p class="text-sm text-gray-600">Monitor your Twitter activity</p>
        </div>
        <div class="flex items-center space-x-4">
          <div
            class="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full"
          >
            Connected
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="p-6 space-y-6">
      <!-- Account Info -->
      <div class="bg-white rounded-lg border border-gray-200 p-6">
        <div class="flex items-center space-x-4">
          <div
            class="w-16 h-16 bg-blue-500 rounded-full flex items-center justify-center"
          >
            <svg
              class="w-8 h-8 text-white"
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"
              />
            </svg>
          </div>
          <div class="flex-1">
            <h2 class="text-xl font-bold text-gray-900">
              {{ dashboardData.handle }}
            </h2>
            <div class="flex space-x-4 text-sm text-gray-600">
              <span>2,847 followers</span>
              <span>934 following</span>
            </div>
          </div>
        </div>
      </div>
      <!-- Stats Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div class="bg-white rounded-lg border border-gray-200 p-4">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <div
                class="w-8 h-8 bg-blue-500 rounded-md flex items-center justify-center"
              >
                <span class="text-white text-sm font-bold">📝</span>
              </div>
            </div>
            <div class="ml-4">
              <dt class="text-sm font-medium text-gray-500 truncate">
                Total Tweets
              </dt>
              <dd class="text-lg font-semibold text-gray-900">
                {{ dashboardData.totalTweets }}
              </dd>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-gray-200 p-4">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <div
                class="w-8 h-8 bg-purple-500 rounded-md flex items-center justify-center"
              >
                <span class="text-white text-sm font-bold">📦</span>
              </div>
            </div>
            <div class="ml-4">
              <dt class="text-sm font-medium text-gray-500 truncate">
                SyftBox Tweets
              </dt>
              <dd class="text-lg font-semibold text-gray-900">
                {{ dashboardData.syftboxTweets }}
              </dd>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-gray-200 p-4">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <div
                class="w-8 h-8 bg-orange-500 rounded-md flex items-center justify-center"
              >
                <span class="text-white text-sm font-bold">📅</span>
              </div>
            </div>
            <div class="ml-4">
              <dt class="text-sm font-medium text-gray-500 truncate">
                Latest Tweet
              </dt>
              <dd class="text-lg font-semibold text-gray-900">
                {{ dashboardData.latestTweetDate }}
              </dd>
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
import { useDataSourcesStore } from "../stores/dataSourcesStore";

export default {
  name: "TwitterDashboard",
  setup() {
    const dataSourcesStore = useDataSourcesStore();

    // Get Twitter data source
    const twitterDataSource = dataSourcesStore.getDataSourceById("twitter");

    return {
      dataSourcesStore,
      dashboardData: twitterDataSource?.dashboardData || {},
    };
  },
};
</script>
