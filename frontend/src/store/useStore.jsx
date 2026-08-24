import { create } from "zustand";

const useStore = create((set) => ({
  count: 0,
  id: "",
  token: "",
  increase: () => set((state) => ({ count: state.count + 1 })),
  increaseAsync: async () => {
    await new Promise((resolve) => setTimeout(resolve, 1000));
    set((state) => ({ count: state.count + 1 }));
  },
  // updateData: (newData) => set((state) => ({ ...state, ...newData })),
  updateData: (newData) => set(newData),
}));

export default useStore;
