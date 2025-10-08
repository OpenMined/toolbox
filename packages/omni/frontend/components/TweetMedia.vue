<template>
  <div v-if="mediaItems.length > 0" class="mb-3">
    <div
      class="grid gap-2 rounded-lg overflow-hidden border border-gray-200 max-w-lg"
      :class="{
        'grid-cols-1': mediaItems.length === 1,
        'grid-cols-2': mediaItems.length === 2 || mediaItems.length === 4,
        'grid-cols-2': mediaItems.length === 3,
      }"
    >
      <div
        v-for="(media, index) in mediaItems"
        :key="index"
        :class="{
          'col-span-2': mediaItems.length === 3 && index === 0,
          'cursor-pointer hover:opacity-90': media.type === 'photo',
        }"
        class="relative bg-gray-100 transition-opacity group rounded-lg overflow-hidden"
        @click="media.type === 'photo' ? openTweetInNewTab() : null"
      >
        <!-- Image -->
        <img
          v-if="media.type === 'photo'"
          :src="media.media_url_https"
          :alt="`Tweet image ${index + 1}`"
          class="w-full h-auto object-contain"
          :style="{ maxHeight: mediaItems.length === 1 ? '400px' : '200px' }"
        />

        <!-- Video -->
        <div
          v-else-if="media.type === 'video'"
          class="relative w-full bg-gray-900"
          :class="{
            'h-64': mediaItems.length === 1,
            'h-48': mediaItems.length === 2,
            'h-32': mediaItems.length > 2,
          }"
        >
          <video
            v-if="playingVideo === media.id"
            :src="getVideoUrl(media)"
            class="w-full h-full object-cover rounded-lg"
            controls
            autoplay
            @ended="playingVideo = null"
          />
          <div
            v-else
            class="w-full h-full flex items-center justify-center cursor-pointer"
            @click="playingVideo = media.id"
          >
            <div class="text-center text-white">
              <svg
                class="w-16 h-16 mx-auto mb-3"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path d="M8 5v14l11-7z" />
              </svg>
              <p class="text-sm font-semibold">Video</p>
              <p class="text-xs opacity-75">Click to play</p>
            </div>
          </div>
        </div>

        <!-- Animated GIF -->
        <img
          v-else-if="media.type === 'animated_gif'"
          :src="media.media_url_https"
          :alt="`Tweet GIF ${index + 1}`"
          class="w-full h-auto object-contain rounded-lg"
          :style="{ maxHeight: mediaItems.length === 1 ? '400px' : '200px' }"
        />

        <!-- Hover overlay for images only -->
        <div
          v-if="media.type === 'photo'"
          class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-10 transition-colors flex items-center justify-center"
        >
          <svg
            class="w-8 h-8 text-white opacity-0 group-hover:opacity-100 transition-opacity"
            fill="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              d="M19 19H5V5h7V3H5c-1.11 0-2 .9-2 2v14c0 1.1 0 2-.9 2-2v-7h-2v7zM14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7z"
            />
          </svg>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { computed, ref } from "vue";

export default {
  name: "TweetMedia",
  props: {
    mediaData: {
      type: String, // JSON string from backend
      default: null,
    },
    tweetUrl: {
      type: String,
      required: true,
    },
  },
  setup(props) {
    const playingVideo = ref(null);

    const mediaItems = computed(() => {
      if (!props.mediaData) return [];

      try {
        const mediaArray = JSON.parse(props.mediaData);
        return mediaArray.map((media) => ({
          type: media.type,
          media_url_https: media.media_url_https,
          url: media.url, // t.co link
          id: media.id_str,
          video_info: media.video_info, // For video URLs
        }));
      } catch (error) {
        console.error("Error parsing media data:", error);
        return [];
      }
    });

    const openTweetInNewTab = () => {
      window.open(props.tweetUrl, "_blank", "noopener,noreferrer");
    };

    const getVideoUrl = (media) => {
      // Extract the best quality video URL from video_info
      if (media.video_info && media.video_info.variants) {
        // Find MP4 variants and get the highest bitrate one
        const mp4Variants = media.video_info.variants.filter(
          (v) => v.content_type === "video/mp4",
        );
        if (mp4Variants.length > 0) {
          // Sort by bitrate descending and take the first one
          const bestQuality = mp4Variants.sort(
            (a, b) => (b.bitrate || 0) - (a.bitrate || 0),
          )[0];
          return bestQuality.url;
        }
      }
      // Fallback to media_url_https
      return media.media_url_https;
    };

    return {
      mediaItems,
      openTweetInNewTab,
      playingVideo,
      getVideoUrl,
    };
  },
};
</script>
