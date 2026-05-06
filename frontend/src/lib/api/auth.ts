import { apiClient } from "./client";
import type {
  RegisterRequest,
  RegisterResponse,
  LoginRequest,
  TokenResponse,
  RefreshRequest,
} from "@/types/api";

export async function register(data: RegisterRequest): Promise<RegisterResponse> {
  const res = await apiClient.post<RegisterResponse>("/auth/register", data);
  return res.data;
}

export async function login(data: LoginRequest): Promise<TokenResponse> {
  const res = await apiClient.post<TokenResponse>("/auth/login", data);
  return res.data;
}

export async function refresh(data: RefreshRequest): Promise<TokenResponse> {
  const res = await apiClient.post<TokenResponse>("/auth/refresh", data);
  return res.data;
}
