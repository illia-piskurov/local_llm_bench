import assert from "node:assert/strict";
import test from "node:test";
import { renderHtmlReport, renderHtmlComparisonReport } from "./html-report.js";
import { coreTasks } from "./tasks.js";
import type { RunManifest } from "./types.js";

const sampleTask1 = coreTasks[0]!;
const sampleTask2 = coreTasks[1]!;

test("renderHtmlReport generates valid standalone HTML report", () => {
  const manifest: RunManifest = {
    schemaVersion: 1,
    id: "2026-08-18T10-00-00Z_test-model_12345678",
    status: "completed",
    startedAt: "2026-08-18T10:00:00.000Z",
    completedAt: "2026-08-18T10:01:00.000Z",
    model: "test-model-7b",
    baseUrl: "http://127.0.0.1:1234/v1",
    hardware: "RTX 4090 | 64GB RAM",
    temperature: 0.2,
    maxTokens: 2048,
    samples: 1,
    taskIds: [sampleTask1.id, sampleTask2.id],
    nodeVersion: process.version,
    candidates: [
      {
        taskId: sampleTask1.id,
        attempt: 1,
        status: "passed",
        durationMs: 150,
        generationMs: 120,
        tokensPerSec: 45,
        completionTokens: 60,
        passed: 5,
        total: 5
      },
      {
        taskId: sampleTask2.id,
        attempt: 1,
        status: "failed",
        durationMs: 180,
        generationMs: 140,
        tokensPerSec: 35,
        completionTokens: 50,
        passed: 3,
        total: 5,
        error: "Test 4 failed: expected X got Y"
      }
    ]
  };

  const candidateDetails = [
    {
      taskId: sampleTask1.id,
      attempt: 1,
      prompt: sampleTask1.prompt,
      code: sampleTask1.referenceCode,
      responseRaw: `\`\`\`js\n${sampleTask1.referenceCode}\n\`\`\``,
      evaluation: {
        status: "passed" as const,
        passed: 5,
        total: 5,
        durationMs: 30,
        tests: [
          { id: "test-1", passed: true },
          { id: "test-2", passed: true }
        ]
      }
    }
  ];

  const html = renderHtmlReport(manifest, candidateDetails);

  assert.match(html, /<!DOCTYPE html>/i);
  assert.match(html, /test-model-7b/);
  assert.match(html, /RTX 4090/);
  assert.match(html, /50%/); // pass@1 accuracy: 1 out of 2 = 50%
  assert.match(html, new RegExp(sampleTask1.id));
  assert.match(html, new RegExp(sampleTask2.id));
  assert.match(html, /Task Specification/);
  assert.match(html, /Solution Code/);
  assert.match(html, /Reference Implementation/);
  assert.match(html, /<script>/);
});

test("renderHtmlComparisonReport generates valid comparison HTML", () => {
  const manifests: RunManifest[] = [
    {
      schemaVersion: 1,
      id: "run-1",
      status: "completed",
      startedAt: "2026-08-18T10:00:00.000Z",
      model: "model-alpha",
      baseUrl: "http://mock/v1",
      hardware: "Test GPU",
      temperature: 0.2,
      maxTokens: 1024,
      samples: 1,
      taskIds: [sampleTask1.id],
      nodeVersion: process.version,
      candidates: [
        {
          taskId: sampleTask1.id,
          attempt: 1,
          status: "passed",
          durationMs: 100,
          generationMs: 80,
          tokensPerSec: 40,
          completionTokens: 50,
          passed: 5,
          total: 5
        }
      ]
    },
    {
      schemaVersion: 1,
      id: "run-2",
      status: "completed",
      startedAt: "2026-08-18T10:05:00.000Z",
      model: "model-beta",
      baseUrl: "http://mock/v1",
      hardware: "Test GPU",
      temperature: 0.2,
      maxTokens: 1024,
      samples: 1,
      taskIds: [sampleTask1.id],
      nodeVersion: process.version,
      candidates: [
        {
          taskId: sampleTask1.id,
          attempt: 1,
          status: "failed",
          durationMs: 120,
          generationMs: 100,
          tokensPerSec: 30,
          completionTokens: 40,
          passed: 2,
          total: 5
        }
      ]
    }
  ];

  const html = renderHtmlComparisonReport(manifests, [sampleTask1]);

  assert.match(html, /<!DOCTYPE html>/i);
  assert.match(html, /Model Benchmark Comparison Matrix/);
  assert.match(html, /model-alpha/);
  assert.match(html, /model-beta/);
  assert.match(html, /✓ PASS/);
  assert.match(html, /FAIL/);
});
