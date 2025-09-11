<template>
  <div class="h-full bg-white">
    <!-- Header -->
    <div class="p-6 border-b border-gray-200">
      <div class="flex items-center justify-between">
        <h2 class="text-2xl font-bold text-gray-900">Create New List</h2>
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

    <!-- Content -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <!-- List Name and Date Range Section -->
      <div class="p-6 border-b border-gray-200">
        <div class="flex items-start justify-between">
          <div class="space-y-4 flex-1">
            <div class="max-w-md">
              <label class="block text-sm font-medium text-gray-900 mb-2">
                List Name
              </label>
              <input
                v-model="listName"
                type="text"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter list name..."
              />
            </div>

            <!-- Date Range (Global) -->
            <div class="max-w-2xl">
              <label class="block text-sm font-medium text-gray-900 mb-3"
                >Date Range (All Sources)</label
              >
              <div class="flex space-x-4">
                <div class="flex-1">
                  <label class="block text-xs text-gray-500 mb-1"
                    >Start Date</label
                  >
                  <input
                    v-model="globalFilters.startDate"
                    type="date"
                    class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div class="flex-1">
                  <label class="block text-xs text-gray-500 mb-1"
                    >End Date</label
                  >
                  <input
                    v-model="globalFilters.endDate"
                    type="date"
                    class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
            </div>
          </div>

          <!-- Create List Button -->
          <div class="ml-8">
            <button
              @click="createList"
              :disabled="!canCreate"
              class="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              Create List
            </button>
          </div>
        </div>
      </div>

      <!-- Main Content Area -->
      <div class="flex-1 flex overflow-hidden">
        <!-- Left Panel - Data Sources -->
        <div class="w-80 border-r border-gray-200 overflow-y-auto">
          <div class="p-6">
            <h3 class="text-sm font-medium text-gray-900 mb-4">
              Select Data Sources
            </h3>
            <div class="space-y-2">
              <div
                v-for="source in dataSources"
                :key="source.id"
                @click="selectSourceForConfiguration(source)"
                class="flex items-center space-x-3 p-3 rounded-lg cursor-pointer transition-colors"
                :class="{
                  'bg-green-50 border border-green-200': addedSources.some(
                    (s) => s.id === source.id,
                  ),
                  'bg-blue-50 border border-blue-200':
                    currentSource?.id === source.id &&
                    !addedSources.some((s) => s.id === source.id),
                  'hover:bg-gray-50':
                    currentSource?.id !== source.id &&
                    !addedSources.some((s) => s.id === source.id),
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
                  <!-- Selection/Added Indicators -->
                  <div
                    v-if="addedSources.some((s) => s.id === source.id)"
                    class="absolute -top-1 -right-1 w-4 h-4 bg-green-600 rounded-full flex items-center justify-center"
                  >
                    <svg
                      class="w-2 h-2 text-white"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fill-rule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clip-rule="evenodd"
                      />
                    </svg>
                  </div>
                  <div
                    v-else-if="currentSource?.id === source.id"
                    class="absolute -top-1 -right-1 w-4 h-4 bg-blue-600 rounded-full flex items-center justify-center"
                  >
                    <div class="w-2 h-2 bg-white rounded-full"></div>
                  </div>
                </div>
                <div class="flex-1">
                  <p class="font-medium text-gray-900">{{ source.name }}</p>
                  <p class="text-sm text-gray-500">{{ source.description }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Panel - Source Configuration -->
        <div class="flex-1 overflow-y-auto">
          <div
            v-if="!currentSource"
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
                    d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                  ></path>
                </svg>
              </div>
              <p class="text-lg">Select a data source to configure</p>
              <p class="text-sm mt-2">
                Choose from the available sources on the left to set up filters
              </p>
            </div>
          </div>

          <div v-else class="p-6">
            <!-- Current Source Configuration -->
            <div class="flex items-center justify-between mb-6">
              <div class="flex items-center space-x-3">
                <div
                  class="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center"
                >
                  <div
                    class="w-5 h-5 rounded"
                    :class="{
                      'bg-blue-500': currentSource.id === 'twitter',
                      'bg-indigo-500': currentSource.id === 'discord',
                      'bg-purple-500': currentSource.id === 'ai-papers',
                    }"
                  ></div>
                </div>
                <h3 class="text-lg font-semibold text-gray-900">
                  {{ currentSource.name }} Filters
                </h3>
              </div>
              <button
                v-if="!addedSources.some((s) => s.id === currentSource.id)"
                @click="addCurrentSource"
                class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Add to List
              </button>
              <div v-else class="flex items-center text-green-600">
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
                Added to List
              </div>
            </div>

            <div class="space-y-4">
              <!-- Authors Filter -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2"
                  >Authors</label
                >
                <div class="flex space-x-2">
                  <input
                    v-model="newAuthor[currentSource.id]"
                    type="text"
                    class="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Add author (default: any author)"
                    @keyup.enter="addAuthor(currentSource.id)"
                  />
                  <button
                    @click="addAuthor(currentSource.id)"
                    :disabled="!newAuthor[currentSource.id]?.trim()"
                    class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
                  >
                    Add
                  </button>
                </div>
                <div
                  v-if="sourceFilters[currentSource.id]?.authors?.length"
                  class="mt-2 flex flex-wrap gap-2"
                >
                  <span
                    v-for="(author, index) in sourceFilters[currentSource.id]
                      .authors"
                    :key="index"
                    class="inline-flex items-center px-2 py-1 rounded-full text-sm bg-blue-100 text-blue-800"
                  >
                    {{ author }}
                    <button
                      @click="removeAuthor(currentSource.id, index)"
                      class="ml-1 text-blue-600 hover:text-blue-800"
                    >
                      ×
                    </button>
                  </span>
                </div>
              </div>

              <!-- RAG Filter -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2"
                  >RAG Filter</label
                >
                <div class="space-y-2">
                  <input
                    v-model="sourceFilters[currentSource.id].ragFilter.query"
                    type="text"
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Semantic search query for content matching"
                  />
                  <div class="grid grid-cols-2 gap-2">
                    <select
                      v-model="sourceFilters[currentSource.id].ragFilter.model"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                    >
                      <option value="">Select model</option>
                      <option value="ollama/nomic-embed-text">
                        ollama/nomic-embed-text
                      </option>
                      <option value="openai/text-embedding-3-small">
                        openai/text-embedding-3-small
                      </option>
                      <option value="openai/text-embedding-3-large">
                        openai/text-embedding-3-large
                      </option>
                    </select>
                    <input
                      v-model.number="
                        sourceFilters[currentSource.id].ragFilter.threshold
                      "
                      type="number"
                      step="0.01"
                      min="0"
                      max="1"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                      placeholder="Threshold (0.7)"
                    />
                  </div>
                </div>
              </div>

              <!-- LLM Filter -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2"
                  >LLM Filter</label
                >
                <textarea
                  v-model="sourceFilters[currentSource.id].llmFilter"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows="2"
                  placeholder="Include only items matching criteria (e.g., 'mentions AI or ML', 'privacy concerns')"
                ></textarea>
              </div>

              <!-- Preview Results -->
              <div class="bg-gray-50 rounded-lg p-3">
                <div class="flex items-center justify-between mb-2">
                  <h4 class="text-sm font-medium text-gray-900">
                    Preview Results
                  </h4>
                  <button
                    @click="refreshPreview(currentSource.id)"
                    class="text-sm text-blue-600 hover:text-blue-800"
                  >
                    Refresh
                  </button>
                </div>
                <div
                  v-if="previewResults[currentSource.id]?.length"
                  class="space-y-1 max-h-24 overflow-y-auto"
                >
                  <div
                    v-for="(item, index) in previewResults[
                      currentSource.id
                    ].slice(0, 3)"
                    :key="index"
                    class="text-sm text-gray-600 p-2 bg-white rounded"
                  >
                    <p class="font-medium leading-tight">
                      {{ item.title || item.content?.substring(0, 50) }}...
                    </p>
                    <p class="text-xs text-gray-500">
                      {{ item.author }} • {{ item.date }}
                    </p>
                  </div>
                  <p
                    v-if="previewResults[currentSource.id].length > 3"
                    class="text-xs text-gray-500 text-center"
                  >
                    +{{ previewResults[currentSource.id].length - 3 }} more
                    items
                  </p>
                </div>
                <div v-else class="text-sm text-gray-500 text-center py-3">
                  No items match the current filters
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
import { ref, computed, reactive, watch } from "vue";
import { useConnectionsStore } from "../stores/connectionsStore";
import { useListsStore } from "../stores/listsStore";
import { DATA_SOURCES } from "../constants/dataSources";

export default {
  name: "CreateList",
  setup() {
    const connectionsStore = useConnectionsStore();
    const listsStore = useListsStore();
    const dataSources = DATA_SOURCES;

    const listName = ref("");
    const currentSource = ref(null);
    const addedSources = ref([]);
    const newAuthor = reactive({});

    const globalFilters = reactive({
      startDate: "",
      endDate: "",
    });

    const sourceFilters = reactive({});
    const previewResults = reactive({});

    const initializeSourceFilter = (sourceId) => {
      if (!sourceFilters[sourceId]) {
        sourceFilters[sourceId] = {
          authors: [],
          llmFilter: "",
          ragFilter: {
            query: "",
            model: "",
            threshold: 0.7,
          },
        };
      }
    };

    const selectSourceForConfiguration = (source) => {
      currentSource.value = source;
      initializeSourceFilter(source.id);
      if (!previewResults[source.id]) {
        generateMockPreview(source.id);
      }
    };

    const addCurrentSource = () => {
      if (
        currentSource.value &&
        !addedSources.value.some((s) => s.id === currentSource.value.id)
      ) {
        addedSources.value.push({
          ...currentSource.value,
          filters: { ...sourceFilters[currentSource.value.id] },
        });
      }
    };

    const addAuthor = (sourceId) => {
      const author = newAuthor[sourceId]?.trim();
      if (
        author &&
        sourceFilters[sourceId] &&
        !sourceFilters[sourceId].authors.includes(author)
      ) {
        sourceFilters[sourceId].authors.push(author);
        newAuthor[sourceId] = "";
        generateMockPreview(sourceId);
      }
    };

    const removeAuthor = (sourceId, index) => {
      if (sourceFilters[sourceId]) {
        sourceFilters[sourceId].authors.splice(index, 1);
        generateMockPreview(sourceId);
      }
    };

    const generateMockPreview = (sourceId) => {
      // Mock preview data based on source type
      const mockData = {
        twitter: [
          {
            title: "AI breakthrough in neural networks",
            author: "@researcher",
            date: "2h ago",
          },
          {
            title: "Machine learning applications in healthcare",
            author: "@medtech",
            date: "4h ago",
          },
          {
            title: "The future of artificial intelligence",
            author: "@futurist",
            date: "6h ago",
          },
          {
            title: "Deep learning optimization techniques",
            author: "@mlexpert",
            date: "8h ago",
          },
          {
            title: "Ethics in AI development",
            author: "@ethicsai",
            date: "10h ago",
          },
        ],
        discord: [
          {
            content: "Discussion about transformer architectures",
            author: "AIResearcher",
            date: "1h ago",
          },
          {
            content: "Debugging CUDA memory issues",
            author: "DevOps_Master",
            date: "3h ago",
          },
          {
            content: "Paper review: Attention mechanisms",
            author: "PaperReviewer",
            date: "5h ago",
          },
          {
            content: "Model deployment best practices",
            author: "MLOps_Pro",
            date: "7h ago",
          },
        ],
        "ai-papers": [
          {
            title: "Attention Is All You Need: Modern Applications",
            author: "Smith et al.",
            date: "Jan 15",
          },
          {
            title: "Constitutional AI: Safety in Large Models",
            author: "Brown et al.",
            date: "Jan 14",
          },
          {
            title: "Chain-of-Thought Reasoning in LLMs",
            author: "Johnson et al.",
            date: "Jan 13",
          },
          {
            title: "Retrieval-Augmented Generation Methods",
            author: "Wilson et al.",
            date: "Jan 12",
          },
        ],
      };

      // Filter based on authors if specified
      let filteredData = mockData[sourceId] || [];
      if (sourceFilters[sourceId]?.authors?.length > 0) {
        filteredData = filteredData.filter((item) =>
          sourceFilters[sourceId].authors.some((author) =>
            item.author.toLowerCase().includes(author.toLowerCase()),
          ),
        );
      }

      previewResults[sourceId] = filteredData;
    };

    const refreshPreview = (sourceId) => {
      generateMockPreview(sourceId);
    };

    const canCreate = computed(() => {
      return listName.value.trim() && addedSources.value.length > 0;
    });

    const createList = () => {
      if (!canCreate.value) return;

      const newList = {
        name: listName.value.trim(),
        sources: addedSources.value,
        globalFilters: { ...globalFilters },
        itemCount: addedSources.value.reduce((sum, source) => {
          return sum + (previewResults[source.id]?.length || 0);
        }, 0),
      };

      listsStore.addList(newList);
      connectionsStore.closeDashboard();
    };

    return {
      connectionsStore,
      listsStore,
      dataSources,
      listName,
      currentSource,
      addedSources,
      newAuthor,
      globalFilters,
      sourceFilters,
      previewResults,
      selectSourceForConfiguration,
      addCurrentSource,
      addAuthor,
      removeAuthor,
      refreshPreview,
      canCreate,
      createList,
    };
  },
};
</script>
