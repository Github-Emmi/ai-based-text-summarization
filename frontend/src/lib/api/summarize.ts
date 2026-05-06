import { apiClient } from "./client";
import type { SummarizeTextRequest, SummaryResponse } from "@/types/api";

export async function summarizeText(
  data: SummarizeTextRequest
): Promise<SummaryResponse> {
  const res = await apiClient.post<SummaryResponse>(
    "/api/v1/summarize/text",
    data
  );
  return res.data;
}

export async function summarizePdf(
  file: File,
  params?: { format?: string; summary_length?: string }
): Promise<SummaryResponse> {
  const form = new FormData();
  form.append("file", file);
  if (params?.format) form.append("format", params.format);
  if (params?.summary_length) form.append("summary_length", params.summary_length);

  const res = await apiClient.post<SummaryResponse>(
    "/api/v1/summarize/pdf",
    form
    // Do NOT set Content-Type manually — browser must set it with the multipart boundary
  );
  return res.data;
}
