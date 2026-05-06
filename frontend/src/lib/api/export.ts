import { apiClient } from "./client";

/**
 * Download a summary as PDF. Triggers a browser download.
 */
export async function exportSummary(
  summaryId: string,
  filename = "summary.pdf"
): Promise<void> {
  const res = await apiClient.get(`/api/v1/export/${summaryId}`, {
    responseType: "blob",
  });

  const url = URL.createObjectURL(new Blob([res.data as BlobPart]));
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
