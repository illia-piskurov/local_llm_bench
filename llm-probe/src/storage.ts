import { appendFile, mkdir, readFile, readdir, writeFile } from "node:fs/promises";
import { basename, join, resolve } from "node:path";
import { randomUUID } from "node:crypto";
import type { CandidateRecord, ChatCompletion, ChatCompletionRequest, EvaluationResult, EvaluationStatus, RunEvent, RunManifest } from "./types.js";

export class RunStorage {
  readonly dir: string;
  private manifest: RunManifest;

  private constructor(dir: string, manifest: RunManifest) {
    this.dir = dir;
    this.manifest = manifest;
  }

  static async create(options: Omit<RunManifest, "schemaVersion" | "id" | "status" | "startedAt" | "nodeVersion" | "candidates"> & { runsDir: string }): Promise<RunStorage> {
    const startedAt = new Date().toISOString();
    const safeModel = options.model.replace(/[^a-zA-Z0-9._-]+/g, "-").slice(0, 48) || "model";
    const id = `${startedAt.replace(/[:.]/g, "-")}_${safeModel}_${randomUUID().slice(0, 8)}`;
    const dir = join(resolve(options.runsDir), id);
    const manifest: RunManifest = {
      schemaVersion: 1,
      id,
      status: "running",
      startedAt,
      model: options.model,
      baseUrl: options.baseUrl,
      ...(options.hardware !== undefined ? { hardware: options.hardware } : {}),
      temperature: options.temperature,
      maxTokens: options.maxTokens,
      samples: options.samples,
      ...(options.repairs !== undefined ? { repairs: options.repairs } : {}),
      taskIds: options.taskIds,
      nodeVersion: process.version,
      candidates: []
    };
    await mkdir(dir, { recursive: true });
    await mkdir(join(dir, "candidates"), { recursive: true });
    const storage = new RunStorage(dir, manifest);
    await storage.writeManifest();
    await storage.event({ type: "run_started" });
    return storage;
  }

  static async list(runsDir: string): Promise<ReadonlyArray<RunManifest>> {
    try {
      const names = await readdir(resolve(runsDir));
      const manifests = await Promise.all(names.map(async (name) => {
        try { return await readJson<RunManifest>(join(resolve(runsDir), name, "manifest.json")); } catch { return undefined; }
      }));
      return manifests.filter((value): value is RunManifest => value !== undefined).sort((a, b) => b.startedAt.localeCompare(a.startedAt));
    } catch { return []; }
  }

  static async open(runsDir: string, selector: string): Promise<RunStorage> {
    const manifests = await RunStorage.list(runsDir);
    const manifest = selector === "latest" ? manifests[0] : manifests.find((item) => item.id === selector || basename(item.id) === selector);
    if (!manifest) throw new Error(`Run not found: ${selector}`);
    return new RunStorage(join(resolve(runsDir), manifest.id), manifest);
  }

  getManifest(): RunManifest { return this.manifest; }

  async event(event: Omit<RunEvent, "at">): Promise<void> {
    await appendFile(join(this.dir, "events.jsonl"), `${JSON.stringify({ at: new Date().toISOString(), ...event })}\n`, "utf8");
  }

  async writeCandidate(taskId: string, attempt: number, files: {
    readonly request: ChatCompletionRequest;
    readonly prompt: string;
    readonly response?: ChatCompletion;
    readonly code?: string;
    readonly evaluation?: EvaluationResult;
    readonly error?: unknown;
  }, repairAttempt?: number): Promise<void> {
    const baseDir = join(this.dir, "candidates", taskId, String(attempt).padStart(2, "0"));
    const dir = repairAttempt ? join(baseDir, `repair_${repairAttempt}`) : baseDir;
    await mkdir(dir, { recursive: true });
    await writeJson(join(dir, "request.json"), files.request);
    await writeFile(join(dir, "prompt.txt"), files.prompt, "utf8");
    if (files.response) {
      await writeFile(join(dir, "response.raw.txt"), files.response.content, "utf8");
      await writeJson(join(dir, "response.json"), files.response.raw);
    }
    if (files.code !== undefined) await writeFile(join(dir, "solution.js"), files.code, "utf8");
    if (files.evaluation) await writeJson(join(dir, "evaluation.json"), files.evaluation);
    if (files.error !== undefined) await writeJson(join(dir, "error.json"), files.error);
  }

  async record(candidate: CandidateRecord): Promise<void> {
    this.manifest = { ...this.manifest, candidates: [...this.manifest.candidates, candidate] };
    await this.writeManifest();
  }

  async setRunning(): Promise<void> {
    this.manifest = { ...this.manifest, status: "running" };
    await this.writeManifest();
    await this.event({ type: "run_resumed" });
  }

  async finish(status: "completed" | "partial"): Promise<void> {
    this.manifest = { ...this.manifest, status, completedAt: new Date().toISOString() };
    await this.writeManifest();
    await this.event({ type: "run_finished", detail: { status } });
  }

  async readText(relativePath: string): Promise<string> {
    return readFile(join(this.dir, relativePath), "utf8");
  }

  async loadCandidateDetails(): Promise<Array<{
    readonly taskId: string;
    readonly attempt: number;
    readonly repairAttempt?: number | undefined;
    readonly repairedFrom?: EvaluationStatus | "provider_error" | "extract_error" | undefined;
    readonly prompt?: string | undefined;
    readonly code?: string | undefined;
    readonly responseRaw?: string | undefined;
    readonly evaluation?: EvaluationResult | undefined;
    readonly error?: { message?: string } | undefined;
  }>> {
    const list: Array<{
      taskId: string;
      attempt: number;
      repairAttempt?: number | undefined;
      repairedFrom?: EvaluationStatus | "provider_error" | "extract_error" | undefined;
      prompt?: string | undefined;
      code?: string | undefined;
      responseRaw?: string | undefined;
      evaluation?: EvaluationResult | undefined;
      error?: { message?: string } | undefined;
    }> = [];

    for (const cand of this.manifest.candidates) {
      const baseDir = join(this.dir, "candidates", cand.taskId, String(cand.attempt).padStart(2, "0"));
      const dir = cand.repairAttempt ? join(baseDir, `repair_${cand.repairAttempt}`) : baseDir;
      let prompt: string | undefined;
      let code: string | undefined;
      let responseRaw: string | undefined;
      let evaluation: EvaluationResult | undefined;
      let error: { message?: string } | undefined;

      try { prompt = await readFile(join(dir, "prompt.txt"), "utf8"); } catch {}
      try { code = await readFile(join(dir, "solution.js"), "utf8"); } catch {}
      try { responseRaw = await readFile(join(dir, "response.raw.txt"), "utf8"); } catch {}
      try { evaluation = await readJson<EvaluationResult>(join(dir, "evaluation.json")); } catch {}
      try { error = await readJson<{ message?: string }>(join(dir, "error.json")); } catch {}

      list.push({
        taskId: cand.taskId,
        attempt: cand.attempt,
        repairAttempt: cand.repairAttempt,
        repairedFrom: cand.repairedFrom,
        prompt,
        code,
        responseRaw,
        evaluation,
        error
      });
    }

    return list;
  }

  private writeManifest(): Promise<void> {
    return writeJson(join(this.dir, "manifest.json"), this.manifest);
  }
}

async function writeJson(path: string, value: unknown): Promise<void> {
  await writeFile(path, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

async function readJson<T>(path: string): Promise<T> {
  return JSON.parse(await readFile(path, "utf8")) as T;
}
