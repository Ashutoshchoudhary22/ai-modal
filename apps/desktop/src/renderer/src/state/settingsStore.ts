import { create } from "zustand";
import type { ApiHealthStatus, DesktopSettings } from "@shared/types";
import { checkHealth } from "../api/client";

interface SettingsStore {
  settings: DesktopSettings | null;
  apiStatus: ApiHealthStatus;
  agentStatus: ApiHealthStatus;
  provider: string | null;
  modelId: string | null;
  loadSettings: () => Promise<void>;
  updateSettings: (partial: Partial<DesktopSettings>) => Promise<void>;
  refreshHealth: () => Promise<void>;
}

export const useSettingsStore = create<SettingsStore>((set, get) => ({
  settings: null,
  apiStatus: "connecting",
  agentStatus: "connecting",
  provider: null,
  modelId: null,

  loadSettings: async () => {
    const settings = await window.desktop.settings.get();
    set({ settings });
    const { useCompletionStore } = await import("../features/completion/completionStore");
    useCompletionStore.getState().setEnabled(settings.inlineCompletionEnabled);
    await get().refreshHealth();
  },

  updateSettings: async (partial) => {
    const settings = await window.desktop.settings.set(partial);
    set({ settings });
    await get().refreshHealth();
  },

  refreshHealth: async () => {
    const settings = get().settings;
    if (!settings) return;
    set({ apiStatus: "connecting", agentStatus: "connecting" });
    const api = await checkHealth(settings.apiUrl);
    const agent = await checkHealth(settings.agentUrl);
    set({
      apiStatus: api.status,
      agentStatus: agent.status,
      provider: api.ready?.provider ?? null,
      modelId: api.ready?.model_id ?? null,
    });
  },
}));
