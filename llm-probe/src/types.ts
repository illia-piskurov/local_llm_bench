export type Json = null | boolean | number | string | Json[] | { [key: string]: Json };

export type TaskCategory = "strings" | "collections" | "numbers" | "structures" | "algorithms" | "correctness" | "product" | "evolution";

export type EvaluationStatus =
  | "passed"
  | "failed"
  | "compile_error"
  | "runtime_error"
  | "timeout"
  | "invalid_output"
  | "worker_error";

export interface TestCase {
  readonly id: string;
  readonly input: Json;
  readonly expected: Json;
}

export interface Task {
  readonly id: string;
  readonly category: TaskCategory;
  readonly title: string;
  readonly prompt: string;
  readonly examples: ReadonlyArray<TestCase>;
  readonly tests: ReadonlyArray<TestCase>;
  readonly referenceCode: string;
  readonly mutants: ReadonlyArray<string>;
  readonly limits?: {
    readonly testMs?: number;
    readonly memoryMb?: number;
    readonly stackKb?: number;
  };
}

export interface TestResult {
  readonly id: string;
  readonly passed: boolean;
  readonly error?: string;
}

export interface EvaluationResult {
  readonly status: EvaluationStatus;
  readonly passed: number;
  readonly total: number;
  readonly tests: ReadonlyArray<TestResult>;
  readonly durationMs: number;
  readonly error?: string;
}

export interface EvaluationRequest {
  readonly code: string;
  readonly task: Task;
}

export interface ChatMessage {
  readonly role: "system" | "user" | "assistant";
  readonly content: string;
}

export interface ChatCompletionRequest {
  readonly model: string;
  readonly messages: ReadonlyArray<ChatMessage>;
  readonly temperature: number;
  readonly max_tokens: number;
  readonly stream: false;
}

export interface ModelInfo {
  readonly id: string;
}

export interface ChatCompletion {
  readonly content: string;
  readonly finishReason?: string;
  readonly usage?: Json;
  readonly raw: Json;
  readonly durationMs: number;
}

export interface CandidateRecord {
  readonly taskId: string;
  readonly attempt: number;
  readonly repairAttempt?: number;
  readonly status: EvaluationStatus | "provider_error" | "extract_error";
  readonly durationMs: number;
  readonly generationMs?: number;
  readonly finishReason?: string;
  readonly usage?: Json;
  readonly completionTokens?: number;
  readonly tokensPerSec?: number;
  readonly passed?: number;
  readonly total?: number;
  readonly error?: string;
  readonly repairedFrom?: EvaluationStatus | "provider_error" | "extract_error";
}

export interface RunManifest {
  readonly schemaVersion: 1;
  readonly id: string;
  readonly status: "running" | "completed" | "partial";
  readonly startedAt: string;
  readonly completedAt?: string;
  readonly model: string;
  readonly baseUrl: string;
  readonly hardware?: string;
  readonly temperature: number;
  readonly maxTokens: number;
  readonly samples: number;
  readonly repairs?: number;
  readonly taskIds: ReadonlyArray<string>;
  readonly nodeVersion: string;
  readonly candidates: ReadonlyArray<CandidateRecord>;
}

export interface RunEvent {
  readonly at: string;
  readonly type: "run_started" | "run_resumed" | "request_started" | "response_received" | "provider_error" | "extract_error" | "evaluation_finished" | "repair_started" | "repair_finished" | "run_error" | "run_finished";
  readonly taskId?: string;
  readonly attempt?: number;
  readonly repairAttempt?: number;
  readonly detail?: Json;
}
