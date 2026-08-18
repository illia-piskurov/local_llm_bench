import assert from "node:assert/strict";
import test from "node:test";
import { evaluate } from "./index.js";
import { coreTasks } from "../tasks.js";

const sampleTask = coreTasks[0];
if (!sampleTask) throw new Error("Missing sample test task");

test("evaluates a correct solve export", async () => {
  const result = await evaluate({
    task: sampleTask,
    code: sampleTask.referenceCode
  });
  assert.equal(result.status, "passed");
  assert.equal(result.passed, result.total);
});

test("reports a compilation error", async () => {
  const result = await evaluate({ task: sampleTask, code: "export function solve( {" });
  assert.equal(result.status, "compile_error");
});

test("reports a runtime error", async () => {
  const result = await evaluate({ task: sampleTask, code: "export function solve() { throw new Error('boom'); }" });
  assert.equal(result.status, "runtime_error");
});

test("reports a wrong answer without treating it as a pass", async () => {
  const result = await evaluate({ task: sampleTask, code: "export function solve() { return 'completely_wrong'; }" });
  assert.equal(result.status, "failed");
  assert.ok(result.passed < result.total);
});

test("interrupts an infinite loop", async () => {
  const result = await evaluate({ task: sampleTask, code: "export function solve() { while (true) {} }" });
  assert.equal(result.status, "timeout");
});
