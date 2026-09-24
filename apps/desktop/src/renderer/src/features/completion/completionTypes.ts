export interface CompletionPosition {
  line: number;
  column: number;
}

export interface CompletionContextPayload {
  nearby_code?: string;
  imports?: string[];
  symbols?: string[];
  repository_context?: string;
  current_function?: string;
}

export interface CompletionRequestPayload {
  request_id: string;
  workspace_id?: string;
  file_path: string;
  language: string;
  prefix: string;
  suffix: string;
  cursor: CompletionPosition;
  document_version: number;
  context: CompletionContextPayload;
  options: {
    max_tokens: number;
    temperature: number;
    context_lines: number;
  };
  model: string;
  trigger_kind: "automatic" | "manual";
}

export interface CompletionResponsePayload {
  request_id: string;
  completion: { text: string; confidence?: number | null };
  model: string;
  provider: string;
  latency_ms?: number;
}

export type CompletionStatus =
  | "ready"
  | "generating"
  | "disabled"
  | "offline"
  | "error";

export interface CompletionTelemetry {
  requested: number;
  shown: number;
  accepted: number;
  rejected: number;
  cancelled: number;
  stale: number;
  errors: number;
}
