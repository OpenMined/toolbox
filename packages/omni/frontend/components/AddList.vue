<template>
  <div class="h-full bg-white">
    <!-- Header -->
    <div class="p-6 border-b border-gray-200">
      <div class="flex items-center justify-between">
        <h2 class="text-2xl font-bold text-gray-900">Add List</h2>
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

    <!-- Content -->
    <div class="p-6">
      <div class="text-center text-gray-500 mt-8">
        <p class="text-lg">Add List functionality coming soon...</p>
        <p class="text-sm mt-2">
          This will allow you to create custom lists for organizing your
          content.
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import { useDataSourcesStore } from "../stores/dataSourcesStore";

export default {
  name: "AddList",
  setup() {
    const dataSourcesStore = useDataSourcesStore();

    return {
      dataSourcesStore,
    };
  },
};
</script>
