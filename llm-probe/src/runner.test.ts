import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import type { ModelClient } from "./model-client.js";
import { runBenchmark } from "./runner.js";
import { coreTasks } from "./tasks.js";

const sampleTask = coreTasks[0];
if (!sampleTask) throw new Error("Missing sample task");

test("writes inspectable artifacts for a complete run", async () => {
  const root = await mkdtemp(join(tmpdir(), "llm-probe-test-"));
  const client: ModelClient = {
    async listModels() { return [{ id: "mock-model" }]; },
    async complete() {
      return {
        content: `\`\`\`js\n${sampleTask.referenceCode}\n\`\`\``,
        raw: { choices: [{ message: { content: "mock" } }] },
        durationMs: 1
      };
    }
  };
  try {
    const storage = await runBenchmark({
      client,
      model: "mock-model",
      tasks: [sampleTask],
      samples: 1,
      temperature: 0.2,
      maxTokens: 100,
      baseUrl: "http://mock/v1",
      runsDir: root
    });
    const manifest = storage.getManifest();
    assert.equal(manifest.status, "completed");
    assert.equal(manifest.candidates[0]?.status, "passed");
    assert.match(await readFile(join(storage.dir, "report.md"), "utf8"), /success@1/);
    assert.match(await readFile(join(storage.dir, "candidates", sampleTask.id, "01", "solution.js"), "utf8"), /export function solve/);
    assert.match(await readFile(join(storage.dir, "events.jsonl"), "utf8"), /evaluation_finished/);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("resumes a partial run without re-evaluating completed tasks", async () => {
  const root = await mkdtemp(join(tmpdir(), "llm-probe-resume-"));
  const task1 = coreTasks[0]!;
  const task2 = coreTasks[1]!;
  let completedCount = 0;

  const controller = new AbortController();

  const client: ModelClient = {
    async listModels() { return [{ id: "mock-model" }]; },
    async complete(req) {
      completedCount++;
      // Abort after task 1 completes
      if (completedCount === 1) {
        controller.abort();
      }
      return {
        content: `\`\`\`js\n${task1.referenceCode}\n\`\`\``,
        raw: { choices: [{ message: { content: "mock" } }] },
        durationMs: 1
      };
    }
  };

  try {
    // 1. Initial run interrupted after 1st task
    const storage1 = await runBenchmark({
      client,
      model: "mock-model",
      tasks: [task1, task2],
      samples: 1,
      temperature: 0.2,
      maxTokens: 100,
      baseUrl: "http://mock/v1",
      runsDir: root,
      signal: controller.signal
    });

    const manifest1 = storage1.getManifest();
    assert.equal(manifest1.status, "partial");
    assert.equal(manifest1.candidates.length, 1);
    assert.equal(completedCount, 1);

    // 2. Resume the run
    const { resumeBenchmark } = await import("./runner.js");
    const storage2 = await resumeBenchmark({
      storage: storage1,
      client,
      runsDir: root
    });

    const manifest2 = storage2.getManifest();
    assert.equal(manifest2.status, "completed");
    assert.equal(manifest2.candidates.length, 2);
    // completedCount should be 2, meaning task 1 was NOT re-evaluated!
    assert.equal(completedCount, 2);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("handles extract_error when response does not contain solve function", async () => {
  const root = await mkdtemp(join(tmpdir(), "llm-probe-extract-"));
  const client: ModelClient = {
    async listModels() { return [{ id: "mock-model" }]; },
    async complete() {
      return {
        content: "I am sorry, I cannot solve this problem for you.",
        raw: { choices: [{ message: { content: "I am sorry..." } }] },
        durationMs: 10
      };
    }
  };

  try {
    const storage = await runBenchmark({
      client,
      model: "mock-model",
      tasks: [sampleTask],
      samples: 1,
      temperature: 0.2,
      maxTokens: 100,
      baseUrl: "http://mock/v1",
      runsDir: root
    });

    const manifest = storage.getManifest();
    assert.equal(manifest.status, "completed");
    assert.equal(manifest.candidates[0]?.status, "extract_error");
    assert.match(manifest.candidates[0]?.error ?? "", /did not contain export function solve/);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("handles extract_error when finish_reason is length (truncated response)", async () => {
  const root = await mkdtemp(join(tmpdir(), "llm-probe-length-"));
  const client: ModelClient = {
    async listModels() { return [{ id: "mock-model" }]; },
    async complete() {
      return {
        content: "I was explaining the algorithm but ran out of tokens before generating the code block",
        finishReason: "length",
        raw: { choices: [{ message: { content: "..." }, finish_reason: "length" }] },
        durationMs: 20
      };
    }
  };

  try {
    const storage = await runBenchmark({
      client,
      model: "mock-model",
      tasks: [sampleTask],
      samples: 1,
      temperature: 0.2,
      maxTokens: 100,
      baseUrl: "http://mock/v1",
      runsDir: root
    });

    const manifest = storage.getManifest();
    assert.equal(manifest.status, "completed");
    assert.equal(manifest.candidates[0]?.status, "extract_error");
    assert.equal(manifest.candidates[0]?.finishReason, "length");
    assert.match(manifest.candidates[0]?.error ?? "", /finish_reason=length/);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("handles provider_error (HTTP error) gracefully without crashing runner", async () => {
  const root = await mkdtemp(join(tmpdir(), "llm-probe-provider-err-"));
  const client: ModelClient = {
    async listModels() { return [{ id: "mock-model" }]; },
    async complete() {
      throw new Error("HTTP 500: Server Out of Memory");
    }
  };

  try {
    const storage = await runBenchmark({
      client,
      model: "mock-model",
      tasks: [sampleTask],
      samples: 1,
      temperature: 0.2,
      maxTokens: 100,
      baseUrl: "http://mock/v1",
      runsDir: root
    });

    const manifest = storage.getManifest();
    assert.equal(manifest.status, "completed");
    assert.equal(manifest.candidates[0]?.status, "provider_error");
    assert.match(manifest.candidates[0]?.error ?? "", /HTTP 500/);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("records failed candidate evaluation and throughput metrics", async () => {
  const root = await mkdtemp(join(tmpdir(), "llm-probe-fail-eval-"));
  const client: ModelClient = {
    async listModels() { return [{ id: "mock-model" }]; },
    async complete() {
      return {
        content: "```javascript\nexport function solve() { return 'wrong_output'; }\n```",
        finishReason: "stop",
        usage: { completion_tokens: 30, prompt_tokens: 100 },
        raw: { choices: [{ message: { content: "..." } }] },
        durationMs: 50
      };
    }
  };

  try {
    const storage = await runBenchmark({
      client,
      model: "mock-model",
      tasks: [sampleTask],
      samples: 1,
      temperature: 0.2,
      maxTokens: 100,
      baseUrl: "http://mock/v1",
      runsDir: root
    });

    const manifest = storage.getManifest();
    assert.equal(manifest.status, "completed");
    assert.equal(manifest.candidates[0]?.status, "failed");
    assert.equal(manifest.candidates[0]?.completionTokens, 30);
    assert.ok((manifest.candidates[0]?.tokensPerSec ?? 0) > 0);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("executes self-repair feedback loop and records recovery", async () => {
  const root = await mkdtemp(join(tmpdir(), "llm-probe-repair-"));
  let callCount = 0;

  const client: ModelClient = {
    async listModels() { return [{ id: "mock-model" }]; },
    async complete(req) {
      callCount++;
      if (callCount === 1) {
        // Initial call fails: broken solution
        return {
          content: "```javascript\nexport function solve() { return 'broken'; }\n```",
          finishReason: "stop",
          raw: { choices: [{ message: { content: "..." } }] },
          durationMs: 40
        };
      }
      // Second call (repair): receives feedback and returns correct code
      assert.ok(req.messages.some((m) => m.role === "user" && m.content.includes("failed")));
      return {
        content: `\`\`\`javascript\n${sampleTask.referenceCode}\n\`\`\``,
        finishReason: "stop",
        raw: { choices: [{ message: { content: "..." } }] },
        durationMs: 40
      };
    }
  };

  try {
    const storage = await runBenchmark({
      client,
      model: "mock-model",
      tasks: [sampleTask],
      samples: 1,
      repairs: 2,
      temperature: 0.2,
      maxTokens: 100,
      baseUrl: "http://mock/v1",
      runsDir: root
    });

    const manifest = storage.getManifest();
    assert.equal(manifest.status, "completed");
    assert.equal(manifest.repairs, 2);
    assert.equal(manifest.candidates.length, 2);

    // Initial candidate was failed
    assert.equal(manifest.candidates[0]?.status, "failed");
    assert.equal(manifest.candidates[0]?.repairAttempt, 0);

    // Repaired candidate passed
    assert.equal(manifest.candidates[1]?.status, "passed");
    assert.equal(manifest.candidates[1]?.repairAttempt, 1);
    assert.equal(manifest.candidates[1]?.repairedFrom, "failed");

    const mdReport = await readFile(join(storage.dir, "report.md"), "utf8");
    assert.match(mdReport, /success@repair/);
    assert.match(mdReport, /Repair Recovery Rate/);

    const htmlReport = await readFile(join(storage.dir, "report.html"), "utf8");
    assert.match(htmlReport, /Repair #1/);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
