import { requestCompletion } from "../../api/completion";
import { useCompletionStore } from "./completionStore";
import { collectCompletionContext, type EditorSnapshot } from "./CompletionContextCollector";
import { fetchRepositoryContext } from "./repositoryContext";
import {
  calculatePrefix,
  deduplicateCompletion,
  isCompletionAllowed,
  normalizeCompletion,
} from "./completionUtils";

export interface CompletionSettings {
  apiUrl: string;
  indexerUrl: string;
  indexerWorkspaceId: string | null;
  enabled: boolean;
  model: string;
  debounceMs: number;
  maxTokens: number;
  contextLines: number;
  repositoryContextEnabled: boolean;
  maxRequestsPerMinute: number;
  timeoutMs: number;
  triggerOnTyping: boolean;
}

export class CompletionController {
  private debounceTimer: ReturnType<typeof setTimeout> | null = null;
  private abortController: AbortController | null = null;
  private latestRequestId = 0;
  private requestTimestamps: number[] = [];
  private disposed = false;
  private pendingSnapshot: EditorSnapshot | null = null;
  private pendingKind: "automatic" | "manual" = "automatic";

  constructor(private readonly getSettings: () => CompletionSettings) {}

  dispose(): void {
    this.disposed = true;
    this.cancel();
  }

  cancel(): void {
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
      this.debounceTimer = null;
    }
    this.abortController?.abort();
    this.abortController = null;
    useCompletionStore.getState().clearCompletion();
  }

  async provide(
    snapshot: EditorSnapshot,
    kind: "automatic" | "manual",
    token?: { isCancellationRequested: boolean },
  ): Promise<string | null> {
    if (this.disposed) return null;
    const settings = this.getSettings();
    if (!isCompletionAllowed(snapshot.filePath, settings.enabled)) {
      useCompletionStore.getState().setStatus("disabled");
      return null;
    }
    if (kind === "automatic" && !settings.triggerOnTyping) {
      return null;
    }

    return new Promise((resolve) => {
      this.pendingSnapshot = snapshot;
      this.pendingKind = kind;
      if (this.debounceTimer) clearTimeout(this.debounceTimer);
      const delay = kind === "manual" ? 0 : settings.debounceMs;
      this.debounceTimer = setTimeout(() => {
        void this.execute(snapshot, kind, token).then(resolve);
      }, delay);
    });
  }

  private canRequest(settings: CompletionSettings): boolean {
    const now = Date.now();
    this.requestTimestamps = this.requestTimestamps.filter((t) => now - t < 60_000);
    return this.requestTimestamps.length < settings.maxRequestsPerMinute;
  }

  private async execute(
    snapshot: EditorSnapshot,
    kind: "automatic" | "manual",
    token?: { isCancellationRequested: boolean },
  ): Promise<string | null> {
    const settings = this.getSettings();
    if (!settings.apiUrl) {
      useCompletionStore.getState().setStatus("offline");
      return null;
    }
    if (!this.canRequest(settings)) {
      if (kind === "manual") {
        useCompletionStore.getState().setError("COMPLETION_RATE_LIMITED");
      }
      return null;
    }

    const requestNum = ++this.latestRequestId;
    const cursorKey = `${snapshot.filePath}:${snapshot.documentVersion}:${snapshot.line}:${snapshot.column}`;
    const store = useCompletionStore.getState();
    store.incrementTelemetry("requested");
    store.setLoading(true);
    store.setError(null);

    this.abortController?.abort();
    const controller = new AbortController();
    this.abortController = controller;
    const timeout = setTimeout(() => controller.abort(), settings.timeoutMs);
    this.requestTimestamps.push(Date.now());

    let repositoryContext: string | undefined;
    if (
      settings.repositoryContextEnabled &&
      settings.indexerWorkspaceId &&
      settings.indexerUrl
    ) {
      repositoryContext =
        (await fetchRepositoryContext(
          settings.indexerUrl,
          settings.indexerWorkspaceId,
          calculatePrefix(snapshot.content, snapshot.offset),
          controller.signal,
        )) ?? undefined;
    }

    const { prefix, suffix, context } = collectCompletionContext(
      snapshot,
      settings.contextLines,
      repositoryContext,
    );

    try {
      const response = await requestCompletion(
        settings.apiUrl,
        {
          request_id: `req-${requestNum}`,
          workspace_id: snapshot.workspaceId,
          file_path: snapshot.filePath,
          language: snapshot.language,
          prefix,
          suffix,
          cursor: { line: snapshot.line, column: snapshot.column },
          document_version: snapshot.documentVersion,
          context,
          options: {
            max_tokens: settings.maxTokens,
            temperature: 0,
            context_lines: settings.contextLines,
          },
          model: settings.model,
          trigger_kind: kind,
        },
        controller.signal,
      );

      if (this.disposed || token?.isCancellationRequested) return null;
      if (requestNum !== this.latestRequestId) {
        store.incrementTelemetry("stale");
        return null;
      }

      const text = normalizeCompletion(
        deduplicateCompletion(response.completion.text, prefix, suffix),
      );
      if (!text) return null;

      store.setCompletion(text, response.request_id, cursorKey, snapshot.filePath);
      store.setLatency(response.latency_ms ?? 0);
      store.incrementTelemetry("shown");
      return text;
    } catch (err) {
      if (controller.signal.aborted) {
        store.incrementTelemetry("cancelled");
        return null;
      }
      store.incrementTelemetry("errors");
      if (kind === "manual") {
        store.setError(err instanceof Error ? err.message : "Completion failed");
      } else {
        store.setStatus("offline");
      }
      return null;
    } finally {
      clearTimeout(timeout);
      store.setLoading(false);
      if (this.abortController === controller) {
        this.abortController = null;
      }
    }
  }

  acceptCompletion(): void {
    useCompletionStore.getState().incrementTelemetry("accepted");
    useCompletionStore.getState().clearCompletion();
  }

  rejectCompletion(): void {
    useCompletionStore.getState().incrementTelemetry("rejected");
    useCompletionStore.getState().clearCompletion();
  }
}
