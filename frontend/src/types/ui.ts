export type ComponentType =
  | "text"
  | "kpi"
  | "table"
  | "chart"
  | "card"
  | "list"
  | "timeline"
  | "form"
  | "source_refs"
  | "image_viewer"
  | "code_editor"
  | "audio_player"
  | "pdf_viewer";

export type LayoutNode =
  | StackNode
  | GridNode
  | TabsNode
  | SectionNode
  | ComponentNode;

export interface StackNode {
  type: "stack";
  direction: "vertical" | "horizontal";
  children: LayoutNode[];
}

export interface GridNode {
  type: "grid";
  columns: number;
  children: LayoutNode[];
}

export interface TabsNode {
  type: "tabs";
  tabs: { label: string; content: LayoutNode }[];
}

export interface SectionNode {
  type: "section";
  heading: string;
  child: LayoutNode;
}

export interface ComponentNode {
  type: "component";
  component: ComponentType;
  props: Record<string, unknown>;
}

export interface UISchema {
  version: "1.0";
  title: string;
  layout: LayoutNode;
  data_bindings: Record<string, unknown>;
}

// Auth types
export type UserRole = "admin" | "contributor" | "user";

export interface UserResponse {
  user_id: string;
  username: string;
  role: UserRole;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

// API response types
export interface SourceRef {
  record_id: string;
  source_ref: string;
  text: string;
  score: number;
  job_id?: string;
  content_type?: string;
  chunk_index?: number;
}

export interface QueryResponse {
  answer: string;
  sources: SourceRef[];
  ui_schema: UISchema;
  cache_hit: boolean;
}

export interface JobResponse {
  job_id: string;
  status: "PENDING" | "PROCESSING" | "READY" | "FAILED";
  input_type?: string;
  source_ref?: string;
  record_count: number;
  file_size?: number;
  error?: string;
  created_at?: string;
  owner_id?: string;
  visibility?: "private" | "public";
}

export interface IngestResponse {
  job_id: string;
  status: string;
}
