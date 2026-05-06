import { apiClient } from "./client";
import type {
  SummaryResponse,
  PaginatedResponse,
  ListSummariesParams,
  ChatSessionSummary,
  ListChatsParams,
} from "@/types/api";

export async function listSummaries(
  params?: ListSummariesParams
): Promise<PaginatedResponse<SummaryResponse>> {
  const res = await apiClient.get<PaginatedResponse<SummaryResponse>>(
    "/api/v1/history/summaries",
    { params }
  );
  return res.data;
}

export async function getSummary(id: string): Promise<SummaryResponse> {
  const res = await apiClient.get<SummaryResponse>(
    `/api/v1/history/summaries/${id}`
  );
  return res.data;
}

export async function deleteSummary(id: string): Promise<void> {
  await apiClient.delete(`/api/v1/history/summaries/${id}`);
}

export async function listChats(
  params?: ListChatsParams
): Promise<PaginatedResponse<ChatSessionSummary>> {
  const res = await apiClient.get<PaginatedResponse<ChatSessionSummary>>(
    "/api/v1/history/chats",
    { params }
  );
  return res.data;
}
