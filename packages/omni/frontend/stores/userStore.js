import { defineStore } from "pinia";
import { apiClient } from "../api/client.js";

export const useUserStore = defineStore("user", {
  state: () => ({
    currentUser: null,
    isAuthenticated: false,
    loading: false,
    error: null,
    showLoginModal: false,
  }),

  getters: {
    userEmail: (state) => state.currentUser?.email || null,
    isLoggedIn: (state) => state.isAuthenticated && state.currentUser !== null,
  },

  actions: {
    async initializeAuth() {
      this.loading = true;
      this.error = null;

      try {
        // Check localStorage for existing user email
        const storedEmail = localStorage.getItem("userEmail");

        if (storedEmail) {
          // Verify user exists in backend
          const user = await this.getUserByEmail(storedEmail);
          if (user) {
            this.currentUser = user;
            this.isAuthenticated = true;
          } else {
            // Clear invalid stored email
            localStorage.removeItem("userEmail");
            this.showLoginModal = true;
          }
        } else {
          // Development mode: auto-login as dev@example.com
          if (import.meta.env.MODE === "development") {
            await this.loginUser("dev@example.com");
          } else {
            this.showLoginModal = true;
          }
        }
      } catch (error) {
        console.error("Failed to initialize auth:", error);
        this.error = error.message;
        this.showLoginModal = true;
      } finally {
        this.loading = false;
      }
    },

    async registerUser(email) {
      this.loading = true;
      this.error = null;

      try {
        const user = await apiClient.registerUser({ email });
        this.currentUser = user;
        this.isAuthenticated = true;

        // Store in localStorage
        localStorage.setItem("userEmail", email);

        // Close login modal
        this.showLoginModal = false;

        return user;
      } catch (error) {
        console.error("Failed to register user:", error);
        this.error = error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async getUserByEmail(email) {
      try {
        return await apiClient.getUser(email);
      } catch (error) {
        if (error.message.includes("404")) {
          return null; // User not found
        }
        throw error;
      }
    },

    async loginUser(email) {
      this.loading = true;
      this.error = null;

      try {
        // Try to get existing user first
        let user = await this.getUserByEmail(email);

        // If user doesn't exist, register them
        if (!user) {
          user = await apiClient.registerUser({ email });
        }

        this.currentUser = user;
        this.isAuthenticated = true;

        // Store in localStorage
        localStorage.setItem("userEmail", email);

        // Close login modal
        this.showLoginModal = false;

        return user;
      } catch (error) {
        console.error("Failed to login user:", error);
        this.error = error.message;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    logout() {
      this.currentUser = null;
      this.isAuthenticated = false;
      localStorage.removeItem("userEmail");
      this.showLoginModal = true;
    },

    openLoginModal() {
      this.showLoginModal = true;
    },

    closeLoginModal() {
      this.showLoginModal = false;
    },
  },
});
