import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import "./assets/styles.css";
import posthog from "posthog-js";

// Initialize PostHog only in production
if (
  import.meta.env.VITE_POSTHOG_API_KEY &&
  import.meta.env.MODE === "production"
) {
  posthog.init("phc_TropYqZrmdCFGIawoLCB7auDIfBMwjTNJlJbd4EJuQg", {
    api_host: "https://us.i.posthog.com",
  });
}

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
app.mount("#app");
