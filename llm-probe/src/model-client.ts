import type { ChatCompletion, ChatCompletionRequest, Json, ModelInfo } from "./types.js";

export class ProviderError extends Error {
  constructor(
    message: string,
    readonly status?: number,
    readonly body?: string
  ) {
    super(message);
    this.name = "ProviderError";
  }
}

export interface ModelClientOptions {
  /** HTTP request timeout in milliseconds. Default: 120 000. */
  readonly timeoutMs?: number;
  /** API key to send as Bearer token. Optional. */
  readonly apiKey?: string;
}

export interface ModelClient {
  listModels(): Promise<ReadonlyArray<ModelInfo>>;
  complete(request: ChatCompletionRequest, signal?: AbortSignal): Promise<ChatCompletion>;
}

export class OpenAiCompatibleClient implements ModelClient {
  private readonly baseUrl: string;
  private readonly timeoutMs: number;
  private readonly apiKey?: string;

  constructor(baseUrl: string, options?: ModelClientOptions) {
    this.baseUrl = baseUrl.replace(/\/+$/, "");
    this.timeoutMs = options?.timeoutMs ?? 120_000;
    if (options?.apiKey !== undefined) this.apiKey = options.apiKey;
  }

  async listModels(): Promise<ReadonlyArray<ModelInfo>> {
    const response = await this.request("/models", { method: "GET" });
    const body = await jsonBody(response);
    if (!isRecord(body) || !Array.isArray(body.data)) throw new ProviderError("Invalid /models response");
    return body.data.flatMap((entry) => isRecord(entry) && typeof entry.id === "string" ? [{ id: entry.id }] : []);
  }

  async complete(request: ChatCompletionRequest, signal?: AbortSignal): Promise<ChatCompletion> {
    const startedAt = performance.now();
    // Combine caller's signal (abort on Ctrl+C) with a per-request timeout signal.
    const timeoutSignal = AbortSignal.timeout(this.timeoutMs);
    const combinedSignal = signal
      ? AbortSignal.any([signal, timeoutSignal])
      : timeoutSignal;
    const response = await this.request("/chat/completions", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(request),
      signal: combinedSignal
    });
    const raw = await jsonBody(response);
    if (
      !isRecord(raw) ||
      !Array.isArray(raw.choices) ||
      !isRecord(raw.choices[0]) ||
      !isRecord(raw.choices[0].message) ||
      typeof raw.choices[0].message.content !== "string"
    ) {
      throw new ProviderError("Invalid chat completion response", response.status, JSON.stringify(raw));
    }
    const first = raw.choices[0] as Record<string, unknown>;
    const message = first.message as Record<string, unknown>;
    return {
      content: message.content as string,
      ...(typeof first.finish_reason === "string" ? { finishReason: first.finish_reason } : {}),
      ...(isJson(raw.usage) ? { usage: raw.usage } : {}),
      raw: raw as Json,
      durationMs: Math.round(performance.now() - startedAt)
    };
  }

  private async request(path: string, init: RequestInit): Promise<Response> {
    const headers: Record<string, string> = { ...(init.headers as Record<string, string> | undefined) };
    if (this.apiKey) headers["authorization"] = `Bearer ${this.apiKey}`;
    let response: Response;
    try {
      response = await fetch(`${this.baseUrl}${path}`, { ...init, headers });
    } catch (error) {
      // Re-wrap timeout/abort errors with a clear message.
      if (error instanceof Error && (error.name === "TimeoutError" || error.name === "AbortError")) {
        throw new ProviderError(
          error.name === "TimeoutError"
            ? `Request to ${this.baseUrl} timed out after ${this.timeoutMs}ms`
            : `Request to ${this.baseUrl} was aborted`
        );
      }
      throw new ProviderError(
        `Cannot connect to ${this.baseUrl}: ${error instanceof Error ? error.message : String(error)}`
      );
    }
    if (!response.ok) {
      const body = await response.text();
      throw new ProviderError(`Provider returned HTTP ${response.status}`, response.status, body);
    }
    return response;
  }
}

async function jsonBody(response: Response): Promise<unknown> {
  const text = await response.text();
  try {
    return JSON.parse(text);
  } catch {
    throw new ProviderError("Provider returned non-JSON response", response.status, text);
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isJson(value: unknown): value is Json {
  if (value === null || typeof value === "boolean" || typeof value === "string") return true;
  if (typeof value === "number") return Number.isFinite(value);
  if (Array.isArray(value)) return value.every(isJson);
  if (typeof value !== "object") return false;
  return Object.getPrototypeOf(value) === Object.prototype && Object.values(value).every(isJson);
}
