<template>
  <div class="max-w-4xl mx-auto">
    <div class="mb-6">
      <h3 class="text-lg font-semibold text-gray-900 mb-2">Summary</h3>
      <p class="text-sm text-gray-600">
        AI-generated summary of the current list content
      </p>
    </div>

    <div v-if="isLoading" class="flex items-center justify-center py-12">
      <div class="flex items-center space-x-3">
        <div
          class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"
        ></div>
        <p class="text-gray-600">Generating summary...</p>
      </div>
    </div>

    <div
      v-else-if="summary"
      class="bg-blue-50 border border-blue-200 rounded-lg p-6"
    >
      <p class="text-gray-800 leading-relaxed">{{ summary }}</p>
    </div>

    <div v-else class="text-center py-12">
      <p class="text-gray-500 mb-4">No summary available</p>
      <button
        class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
        @click="generateSummary"
      >
        Generate Summary
      </button>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from "vue";
import { useListsStore } from "../stores/listsStore";

export default {
  name: "SummaryView",
  setup() {
    const listsStore = useListsStore();
    const summary = ref("");
    const isLoading = ref(false);

    const generateSummary = async () => {
      isLoading.value = true;
      try {
        summary.value = await listsStore.generateSummary();
      } catch (error) {
        console.error("Failed to generate summary:", error);
      } finally {
        isLoading.value = false;
      }
    };

    onMounted(() => {
      // Auto-generate summary when component mounts
      generateSummary();
    });

    return {
      summary,
      isLoading,
      generateSummary,
    };
  },
};
</script>
