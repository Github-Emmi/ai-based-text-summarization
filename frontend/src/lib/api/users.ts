import { apiClient } from "./client";
import type { UserResponse, UpdateUserRequest } from "@/types/api";

export async function getMe(): Promise<UserResponse> {
  const res = await apiClient.get<UserResponse>("/api/v1/users/me");
  return res.data;
}

export async function updateMe(data: UpdateUserRequest): Promise<UserResponse> {
  const res = await apiClient.patch<UserResponse>("/api/v1/users/me", data);
  return res.data;
}
