import assert from "node:assert/strict";
import test from "node:test";
import { evaluate } from "./evaluator/index.js";
import { coreTasks } from "./tasks.js";

for (const task of coreTasks) {
  test(`[${task.category}] ${task.id}: reference solution passes all tests`, async () => {
    const result = await evaluate({ task, code: task.referenceCode });
    assert.equal(
      result.status,
      "passed",
      `Expected all ${result.total} tests to pass, got ${result.passed}/${result.total}: ${result.error ?? result.tests.filter(t => !t.passed).map(t => t.error).join("; ")}`
    );
  });

  for (let i = 0; i < task.mutants.length; i++) {
    const mutantIndex = i;
    test(`[${task.category}] ${task.id}: mutant #${mutantIndex + 1} fails at least one test`, async () => {
      const result = await evaluate({ task, code: task.mutants[mutantIndex]! });
      assert.notEqual(
        result.status,
        "passed",
        `Mutant #${mutantIndex + 1} for ${task.id} passed all tests — it should fail at least one`
      );
    });
  }
}
