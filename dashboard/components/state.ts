import { create } from "zustand";

type ServerState = {
  state: null | {
    environment: string;
    commit_sha: string;
    branch_name: string;
    start_time: number;
  };
  setState: (newState: {
    environment: string;
    commit_sha: string;
    branch_name: string;
    start_time: number;
  }) => void;
};

export const useServerStore = create<ServerState>((set) => ({
  state: null,
  setState: (newState) => set((state) => ({ state: newState })),
}));
