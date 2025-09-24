<template>
  <!-- Modal Backdrop -->
  <div
    v-if="userStore.showLoginModal"
    class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    @click="handleBackdropClick"
  >
    <!-- Modal Content -->
    <div
      class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6"
      @click.stop
    >
      <!-- Header -->
      <div class="text-center mb-6">
        <div
          class="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4"
        >
          <img
            src="../assets/om-icon.svg"
            alt="OpenMined Logo"
            class="w-8 h-8"
          />
        </div>
        <h2 class="text-xl font-semibold text-gray-900 mb-2">
          Welcome to Omni
        </h2>
        <p class="text-sm text-gray-600">
          Please enter your email address to get started
        </p>
      </div>

      <!-- Form -->
      <form @submit.prevent="handleSubmit">
        <div class="mb-4">
          <label
            for="email"
            class="block text-sm font-medium text-gray-700 mb-2"
          >
            Email Address
          </label>
          <input
            id="email"
            v-model="email"
            type="email"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            :class="{
              'border-red-300 focus:ring-red-500 focus:border-red-500':
                userStore.error,
            }"
            placeholder="Enter your email"
            :disabled="userStore.loading"
          />
        </div>

        <!-- Error Message -->
        <div v-if="userStore.error" class="mb-4">
          <p
            class="text-sm text-red-600 bg-red-50 border border-red-200 rounded-md p-2"
          >
            {{ userStore.error }}
          </p>
        </div>

        <!-- Submit Button -->
        <button
          type="submit"
          :disabled="userStore.loading || !email.trim()"
          class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <span
            v-if="userStore.loading"
            class="flex items-center justify-center"
          >
            <svg
              class="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
              xmlns="http://www.w3.org/2000/svg"
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
            Getting started...
          </span>
          <span v-else>Get Started</span>
        </button>
      </form>

      <!-- Footer -->
      <div class="mt-4 text-center">
        <p class="text-xs text-gray-500">
          No password required. We'll create your account automatically.
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from "vue";
import { useUserStore } from "../stores/userStore";

export default {
  name: "LoginModal",
  setup() {
    const userStore = useUserStore();
    const email = ref("");

    const handleSubmit = async () => {
      if (!email.value.trim()) return;

      try {
        await userStore.loginUser(email.value.trim());
        email.value = "";
      } catch (error) {
        // Error is already handled in the store
        console.error("Login failed:", error);
      }
    };

    const handleBackdropClick = () => {
      // In a real app, you might want to prevent closing the modal
      // if authentication is required. For now, we'll keep it open.
      // userStore.closeLoginModal();
    };

    return {
      userStore,
      email,
      handleSubmit,
      handleBackdropClick,
    };
  },
};
</script>
