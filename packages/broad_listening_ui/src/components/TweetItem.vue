<template>
  <div class="p-4 hover:bg-gray-50 transition-colors">
    <div class="flex space-x-3">
      <!-- Author profile image -->
      <img
        :src="getAuthorAvatarUrl(item.author)"
        :alt="`${item.author.name} avatar`"
        class="w-10 h-10 rounded-full flex-shrink-0"
        @error="onImageError"
      />

      <!-- Tweet content -->
      <div class="flex-1 min-w-0">
        <!-- Author info -->
        <div class="flex items-center space-x-2 mb-2">
          <span class="font-medium text-gray-900">{{ item.author.name }}</span>
          <span class="text-gray-500">{{ item.author.handle }}</span>
          <span class="text-gray-500">·</span>
          <span class="text-gray-500 text-sm">{{ item.timestamp }}</span>
        </div>

        <!-- Tweet text -->
        <p class="text-gray-900 mb-3 leading-relaxed">{{ item.content }}</p>

        <!-- Engagement metrics -->
        <div class="flex items-center space-x-6 text-sm text-gray-500">
          <!-- Twitter logo -->
          <div class="flex items-center">
            <svg
              class="w-4 h-4 text-blue-500"
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"
              />
            </svg>
          </div>

          <div class="flex items-center space-x-1">
            <svg
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
              />
            </svg>
            <span>{{ item.likes }}</span>
          </div>

          <div class="flex items-center space-x-1">
            <svg
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
            <span>{{ item.reactions }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "TweetItem",
  props: {
    item: {
      type: Object,
      required: true,
    },
  },
  methods: {
    getAuthorAvatarUrl(author) {
      // Use the real avatar URL from mock data if available, otherwise use pravatar fallback with unique seed
      if (author.avatarUrl) {
        return author.avatarUrl;
      }
      // Use the handle as a seed to get consistent but unique avatars
      const seed = author.handle.replace("@", "");
      return `https://i.pravatar.cc/128?u=${seed}`;
    },
    onImageError(event) {
      // Fallback to pravatar with a seed based on the author name
      const seed = this.item.author.handle.replace("@", "");
      event.target.src = `https://i.pravatar.cc/128?u=${seed}`;
    },
  },
};
</script>
