// ─── Auth ────────────────────────────────────────────────────────────────────

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface RegisterResponse {
  id: string;
  email: string;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface RefreshRequest {
  refresh_token: string;
}

// ─── Users ───────────────────────────────────────────────────────────────────

export interface UserResponse {
  id: string;
  email: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UpdateUserRequest {
  email?: string;
  password?: string;
}

// ─── Summarize ───────────────────────────────────────────────────────────────

export type SummaryFormat = "paragraph" | "bullets";
export type SummaryLength = "short" | "medium" | "long";
export type SourceType = "text" | "pdf";

export interface SummarizeTextRequest {
  text: string;
  format?: SummaryFormat;
  summary_length?: SummaryLength;
}

export interface SummaryResponse {
  id: string;
  summary: string;
  format: SummaryFormat;
  summary_length: SummaryLength;
  word_count: number;
  language: string;
  model_used: string;
  tokens_used: number;
  keywords: string[];
  source_type: SourceType;
  created_at: string;
  original_filename?: string;
  original_text?: string;
}

// ─── History ─────────────────────────────────────────────────────────────────

export interface Pagination {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  pagination: Pagination;
}

export interface ListSummariesParams {
  page?: number;
  page_size?: number;
  source_type?: SourceType;
  keyword?: string;
}

// ─── Chat ─────────────────────────────────────────────────────────────────────

export interface SendMessageRequest {
  message: string;
  session_id?: string;
  summary_id?: string;
}

export interface SendMessageResponse {
  session_id: string;
  message_id: string;
  reply: string;
  tokens_used: number;
  created_at: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  tokens_used?: number;
  created_at: string;
}

export interface ChatSessionResponse {
  session_id: string;
  title: string;
  summary_id?: string;
  messages: ChatMessage[];
  created_at: string;
}

export interface ChatSessionSummary {
  id: string;
  title: string;
  summary_id?: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface ListChatsParams {
  page?: number;
  page_size?: number;
}
