import { create } from "zustand";

type StoreState = {
  bears: number;
  increasePopulation: () => void;
  removeAllBears: () => void;
};

export const useStore = create<StoreState>((set) => ({
  bears: 0,
  increasePopulation: () => set((state) => ({ bears: state.bears + 1 })),
  removeAllBears: () => set({ bears: 0 }),
}));
