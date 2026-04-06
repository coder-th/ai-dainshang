import { defineStore } from "pinia";
import { ref } from "vue";

export const useTabsStore = defineStore("tabs", () => {
  const tabs = ref([
    { name: "home", path: "/", title: "AI绘画", closable: false },
  ]);
  const activePath = ref("/");

  /** Open or activate a tab based on a route object */
  function openTab(route) {
    const path = route.path;
    const exists = tabs.value.find((t) => t.path === path);
    if (!exists) {
      tabs.value.push({
        name: route.name,
        path,
        title: route.meta?.title || route.name || path,
        closable: route.meta?.closable !== false,
      });
    }
    activePath.value = path;
  }

  /**
   * Close a tab. Returns the path to navigate to, or null if no change needed.
   */
  function closeTab(path) {
    const idx = tabs.value.findIndex((t) => t.path === path);
    if (idx === -1) return null;

    tabs.value.splice(idx, 1);

    // If the closed tab was active, switch to the adjacent one
    if (activePath.value === path) {
      const next = tabs.value[idx] || tabs.value[idx - 1] || tabs.value[0];
      activePath.value = next.path;
      return next.path;
    }
    return null;
  }

  return { tabs, activePath, openTab, closeTab };
});
