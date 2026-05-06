import { create } from "zustand";
import type { UserResponse } from "@/types/api";

interface AuthState {
  accessToken: string | null;
  user: UserResponse | null;
  setAuth: (accessToken: string, user: UserResponse) => void;
  setAccessToken: (token: string) => void;
  setUser: (user: UserResponse) => void;
  clearAuth: () => void;
  isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  accessToken: null,
  user: null,

  setAuth: (accessToken, user) => set({ accessToken, user }),

  setAccessToken: (token) => set({ accessToken: token }),

  setUser: (user) => set({ user }),

  clearAuth: () => set({ accessToken: null, user: null }),

  isAuthenticated: () => get().accessToken !== null,
}));
