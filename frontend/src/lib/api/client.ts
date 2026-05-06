import axios from "axios";
import type { AxiosInstance, InternalAxiosRequestConfig } from "axios";
import { useAuthStore } from "@/lib/store/auth-store";
import type { TokenResponse } from "@/types/api";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
});

// ─── Request interceptor — inject Bearer token ───────────────────────────────
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().accessToken;
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  // When sending FormData, remove the instance-level Content-Type default so
  // the browser/axios can set multipart/form-data with the correct boundary.
  if (config.data instanceof FormData && config.headers) {
    delete config.headers["Content-Type"];
  }
  return config;
});

// ─── Track in-flight refresh to prevent loops ────────────────────────────────
let isRefreshing = false;
let refreshSubscribers: Array<(token: string) => void> = [];

function onRefreshed(token: string) {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
}

function addRefreshSubscriber(cb: (token: string) => void) {
  refreshSubscribers.push(cb);
}

// ─── Response interceptor — refresh on 401 ───────────────────────────────────
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error);
    }

    if (isRefreshing) {
      // Queue the request until token is refreshed
      return new Promise<unknown>((resolve, reject) => {
        addRefreshSubscriber((newToken: string) => {
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          resolve(apiClient(originalRequest));
        });
        // Attach reject to handle the case where refresh fails
        void reject;
      });
    }

    originalRequest._retry = true;
    isRefreshing = true;

    try {
      // Read refresh token from cookie via our Next.js route handler
      const cookieRes = await fetch("/api/auth/get-refresh-token");
      if (!cookieRes.ok) throw new Error("No refresh token");
      const { refresh_token } = (await cookieRes.json()) as {
        refresh_token: string;
      };

      const { data } = await axios.post<TokenResponse>(
        `${BASE_URL}/auth/refresh`,
        { refresh_token }
      );

      useAuthStore.getState().setAccessToken(data.access_token);

      // Persist new refresh token to httpOnly cookie
      await fetch("/api/auth/set-cookie", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: data.refresh_token }),
      });

      onRefreshed(data.access_token);
      originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
      // If the original request body was FormData, remove the Content-Type header so
      // the browser/axios resets it (with the correct multipart boundary) on retry.
      if (originalRequest.data instanceof FormData) {
        delete originalRequest.headers["Content-Type"];
      }
      return apiClient(originalRequest);
    } catch {
      // Refresh failed — sign out
      useAuthStore.getState().clearAuth();
      await fetch("/api/auth/clear-cookie", { method: "POST" });
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
      return Promise.reject(error);
    } finally {
      isRefreshing = false;
    }
  }
);
