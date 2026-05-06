/**
 * Format an ISO date string to a human-readable form.
 * e.g. "Jan 15, 2025 at 3:42 PM"
 */
export function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
}

/**
 * Format a short date (no time).
 * e.g. "Jan 15, 2025"
 */
export function formatShortDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

/**
 * Truncate a string to maxLen characters, appending "…" if truncated.
 */
export function truncate(text: string, maxLen: number): string {
  if (text.length <= maxLen) return text;
  return text.slice(0, maxLen).trimEnd() + "…";
}

/**
 * Format a token count with comma separation.
 * e.g. 1234 → "1,234 tokens"
 */
export function formatTokens(count: number): string {
  return `${count.toLocaleString()} tokens`;
}

/**
 * Convert a source_type value to a display label.
 */
export function sourceTypeLabel(type: string): string {
  return type === "pdf" ? "PDF" : "Text";
}

/**
 * Convert a summary_length value to a display label.
 */
export function summaryLengthLabel(length: string): string {
  const map: Record<string, string> = {
    short: "Short",
    medium: "Medium",
    long: "Long",
  };
  return map[length] ?? length;
}

/**
 * Convert a format value to a display label.
 */
export function formatLabel(format: string): string {
  const map: Record<string, string> = {
    paragraph: "Paragraph",
    bullet_points: "Bullet Points",
    numbered_list: "Numbered List",
  };
  return map[format] ?? format;
}
