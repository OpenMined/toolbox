<template>
  <div class="h-full bg-gray-50 overflow-y-auto">
    <!-- Header -->
    <div class="bg-white border-b border-gray-200 px-6 py-4">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">Discord Dashboard</h1>
          <p class="text-sm text-gray-600">Monitor your Discord activity</p>
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
            class="w-16 h-16 bg-indigo-500 rounded-full flex items-center justify-center"
          >
            <span class="text-white font-bold text-xl">🎮</span>
          </div>
          <div>
            <h2 class="text-xl font-bold text-gray-900">AIDevBot#1234</h2>
            <p class="text-gray-600">Connected to 3 servers</p>
          </div>
        </div>
      </div>

      <!-- Stats Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="bg-white rounded-lg border border-gray-200 p-4">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <div
                class="w-8 h-8 bg-blue-500 rounded-md flex items-center justify-center"
              >
                <span class="text-white text-sm font-bold">#</span>
              </div>
            </div>
            <div class="ml-4">
              <dt class="text-sm font-medium text-gray-500 truncate">
                Total Messages
              </dt>
              <dd class="text-lg font-semibold text-gray-900">
                {{ dashboardData.totalMessages || 0 }}
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
                SyftBox Messages
              </dt>
              <dd class="text-lg font-semibold text-gray-900">342</dd>
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
                Latest Message
              </dt>
              <dd class="text-lg font-semibold text-gray-900">
                {{ dashboardData.latestActivity || "N/A" }}
              </dd>
            </div>
          </div>
        </div>
      </div>

      <!-- Server and Channel Stats -->
      <div class="bg-white rounded-lg border border-gray-200">
        <div class="px-6 py-4 border-b border-gray-200">
          <h3 class="text-lg font-medium text-gray-900">Server Statistics</h3>
        </div>
        <div class="p-6">
          <div class="space-y-4">
            <div
              v-for="server in serverStats"
              :key="server.name"
              class="space-y-2"
            >
              <!-- Server Header -->
              <div
                class="flex items-center justify-between py-2 border-b border-gray-100"
              >
                <div class="flex items-center space-x-3">
                  <div
                    class="w-6 h-6 bg-indigo-500 rounded flex items-center justify-center"
                  >
                    <span class="text-white font-bold text-xs">{{
                      server.name.charAt(0)
                    }}</span>
                  </div>
                  <span class="font-medium text-gray-900">{{
                    server.name
                  }}</span>
                </div>
                <span class="text-sm text-gray-500"
                  >{{ server.totalMessages }} messages</span
                >
              </div>

              <!-- Channels under this server -->
              <div class="ml-9 space-y-1">
                <div
                  v-for="channel in server.channels"
                  :key="channel.name"
                  class="flex items-center justify-between py-1"
                >
                  <div class="flex items-center space-x-2">
                    <span class="text-gray-400 text-sm">#</span>
                    <span class="text-sm text-gray-700">{{
                      channel.name
                    }}</span>
                  </div>
                  <div class="flex items-center space-x-3">
                    <span class="text-xs text-gray-500">{{
                      channel.messageCount
                    }}</span>
                    <div class="w-16 bg-gray-200 rounded-full h-1">
                      <div
                        class="bg-blue-400 h-1 rounded-full"
                        :style="{ width: channel.percentage + '%' }"
                      ></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Embeddings Stats -->
      <div class="bg-white rounded-lg border border-gray-200">
        <div class="px-6 py-4 border-b border-gray-200">
          <h3 class="text-lg font-medium text-gray-900">
            Messages with Embeddings
          </h3>
        </div>
        <div class="p-6">
          <div class="space-y-4">
            <div
              v-for="(count, model) in dashboardData.embeddingCounts || {}"
              :key="model"
              class="flex justify-between items-center"
            >
              <span class="text-sm font-medium text-gray-900">{{ model }}</span>
              <span class="text-sm text-gray-600">{{ count }} messages</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from "vue";
import { useDataSourcesStore } from "../stores/dataSourcesStore";

export default {
  name: "DiscordDashboard",
  setup() {
    const dataSourcesStore = useDataSourcesStore();

    // Get Discord data source
    const discordDataSource = dataSourcesStore.getDataSourceById("discord");

    const serverStats = computed(() => {
      const servers = [
        {
          name: "AI Development Hub",
          channels: [
            { name: "general", messageCount: 1247 },
            { name: "ai-discussion", messageCount: 892 },
            { name: "model-releases", messageCount: 634 },
            { name: "paper-reviews", messageCount: 423 },
          ],
        },
        {
          name: "Machine Learning Research",
          channels: [
            { name: "research-updates", messageCount: 356 },
            { name: "code-sharing", messageCount: 289 },
          ],
        },
        {
          name: "Open Source Contributors",
          channels: [
            { name: "project-showcase", messageCount: 167 },
            { name: "help-wanted", messageCount: 134 },
          ],
        },
      ];

      // Calculate totals and percentages for each server
      return servers.map((server) => {
        const totalMessages = server.channels.reduce(
          (sum, channel) => sum + channel.messageCount,
          0,
        );
        const maxChannelCount = Math.max(
          ...server.channels.map((c) => c.messageCount),
        );

        return {
          ...server,
          totalMessages,
          channels: server.channels.map((channel) => ({
            ...channel,
            percentage: (channel.messageCount / maxChannelCount) * 100,
          })),
        };
      });
    });

    return {
      dataSourcesStore,
      dashboardData: discordDataSource?.dashboardData || {},
      serverStats,
    };
  },
};
</script>
