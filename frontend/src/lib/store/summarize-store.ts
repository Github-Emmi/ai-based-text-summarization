import { create } from "zustand";
import type { SummaryResponse } from "@/types/api";

interface SummarizeState {
  currentResult: SummaryResponse | null;
  isLoading: boolean;
  setResult: (result: SummaryResponse) => void;
  setLoading: (loading: boolean) => void;
  clearResult: () => void;
}

export const useSummarizeStore = create<SummarizeState>((set) => ({
  currentResult: null,
  isLoading: false,

  setResult: (result) => set({ currentResult: result, isLoading: false }),

  setLoading: (loading) => set({ isLoading: loading }),

  clearResult: () => set({ currentResult: null }),
}));
