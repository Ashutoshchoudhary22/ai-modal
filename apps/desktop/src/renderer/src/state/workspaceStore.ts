import { create } from "zustand";
import type { ProjectInfo, RecentWorkspace, WorkspaceState } from "@shared/types";

interface WorkspaceStore {
  workspace: WorkspaceState | null;
  recents: RecentWorkspace[];
  projectInfo: ProjectInfo | null;
  setWorkspace: (ws: WorkspaceState | null) => void;
  setRecents: (recents: RecentWorkspace[]) => void;
  setProjectInfo: (info: ProjectInfo | null) => void;
}

export const useWorkspaceStore = create<WorkspaceStore>((set) => ({
  workspace: null,
  recents: [],
  projectInfo: null,
  setWorkspace: (ws) => set({ workspace: ws }),
  setRecents: (recents) => set({ recents }),
  setProjectInfo: (info) => set({ projectInfo: info }),
}));
