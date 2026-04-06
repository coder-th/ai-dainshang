import { createRouter, createWebHistory } from "vue-router";
import HomeView from "@/views/HomeView.vue";

const router = createRouter({
  history: createWebHistory("/"),
  routes: [
    {
      path: "/",
      component: () => import("@/layouts/MainLayout.vue"),
      children: [
        {
          path: "",
          name: "home",
          component: HomeView,
          meta: { title: "AI绘画", icon: "House", closable: false },
        },
        {
          path: "video",
          name: "video",
          component: () => import("@/views/VideoView.vue"),
          meta: { title: "AI视频", icon: "VideoCamera", closable: true },
        },
        {
          path: "settings",
          name: "settings",
          component: () => import("@/views/SettingsView.vue"),
          meta: { title: "设置", icon: "Setting", closable: true },
        },
      ],
    },
  ],
});

router.beforeEach((to) => {
  document.title = to.meta.title || "AI创意工坊";
});

export default router;
