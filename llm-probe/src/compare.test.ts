import assert from "node:assert/strict";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { renderComparisonReport, runCompare } from "./compare.js";
import type { ModelClient } from "./model-client.js";
import { coreTasks } from "./tasks.js";
import type { RunManifest } from "./types.js";

const sampleTask1 = coreTasks[0]!;
const sampleTask2 = coreTasks[1]!;

test("renderComparisonReport generates summary table and task matrix", () => {
  const manifests: RunManifest[] = [
    {
      schemaVersion: 1,
      id: "run-model-a",
      status: "completed",
      startedAt: "2026-08-18T10:00:00.000Z",
      model: "model-a",
      baseUrl: "http://mock/v1",
      hardware: "Test Hardware",
      temperature: 0.2,
      maxTokens: 1024,
      samples: 1,
      taskIds: [sampleTask1.id, sampleTask2.id],
      nodeVersion: process.version,
      candidates: [
        {
          taskId: sampleTask1.id,
          attempt: 1,
          status: "passed",
          durationMs: 100,
          generationMs: 80,
          tokensPerSec: 25,
          completionTokens: 50,
          passed: 5,
          total: 5
        },
        {
          taskId: sampleTask2.id,
          attempt: 1,
          status: "failed",
          durationMs: 120,
          generationMs: 100,
          tokensPerSec: 20,
          completionTokens: 40,
          passed: 2,
          total: 5
        }
      ]
    },
    {
      schemaVersion: 1,
      id: "run-model-b",
      status: "completed",
      startedAt: "2026-08-18T10:05:00.000Z",
      model: "model-b",
      baseUrl: "http://mock/v1",
      hardware: "Test Hardware",
      temperature: 0.2,
      maxTokens: 1024,
      samples: 1,
      taskIds: [sampleTask1.id, sampleTask2.id],
      nodeVersion: process.version,
      candidates: [
        {
          taskId: sampleTask1.id,
          attempt: 1,
          status: "passed",
          durationMs: 90,
          generationMs: 70,
          tokensPerSec: 30,
          completionTokens: 45,
          passed: 5,
          total: 5
        },
        {
          taskId: sampleTask2.id,
          attempt: 1,
          status: "passed",
          durationMs: 110,
          generationMs: 90,
          tokensPerSec: 28,
          completionTokens: 60,
          passed: 5,
          total: 5
        }
      ]
    }
  ];

  const report = renderComparisonReport(manifests, [sampleTask1, sampleTask2]);

  assert.match(report, /Model Benchmark Comparison Matrix/);
  assert.match(report, /`model-a`/);
  assert.match(report, /`model-b`/);
  assert.match(report, /Task-by-Task Matrix/);
  assert.match(report, /PASS/);
  assert.match(report, /FAIL/);
});

test("runCompare executes benchmark across multiple models in sequence", async () => {
  const root = await mkdtemp(join(tmpdir(), "llm-probe-compare-"));
  const modelsExecuted: string[] = [];

  const client: ModelClient = {
    async listModels() { return [{ id: "model-1" }, { id: "model-2" }]; },
    async complete(req) {
      if (!modelsExecuted.includes(req.model)) modelsExecuted.push(req.model);
      return {
        content: `\`\`\`js\n${sampleTask1.referenceCode}\n\`\`\``,
        raw: { choices: [{ message: { content: "mock" } }] },
        durationMs: 1
      };
    }
  };

  try {
    const storages = await runCompare({
      client,
      models: ["model-1", "model-2"],
      tasks: [sampleTask1],
      samples: 1,
      temperature: 0.2,
      maxTokens: 100,
      baseUrl: "http://mock/v1",
      hardware: "Test Hardware",
      runsDir: root
    });

    assert.equal(storages.length, 2);
    assert.deepEqual(modelsExecuted, ["model-1", "model-2"]);
    assert.equal(storages[0]!.getManifest().model, "model-1");
    assert.equal(storages[1]!.getManifest().model, "model-2");
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
