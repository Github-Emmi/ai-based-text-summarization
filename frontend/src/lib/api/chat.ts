import { apiClient } from "./client";
import type {
  SendMessageRequest,
  SendMessageResponse,
  ChatSessionResponse,
} from "@/types/api";

export async function sendMessage(
  data: SendMessageRequest
): Promise<SendMessageResponse> {
  const res = await apiClient.post<SendMessageResponse>("/api/v1/chat", data);
  return res.data;
}

export async function getSession(
  sessionId: string
): Promise<ChatSessionResponse> {
  const res = await apiClient.get<ChatSessionResponse>(
    `/api/v1/chat/${sessionId}`
  );
  return res.data;
}

export async function deleteSession(sessionId: string): Promise<void> {
  await apiClient.delete(`/api/v1/chat/${sessionId}`);
}
