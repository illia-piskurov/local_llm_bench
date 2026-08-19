import { strict as assert } from 'assert';

export function solve(input) {
  let maxLength = 0;
  let start = 0;
  const charIndexMap = {};

  for (let i = 0; i < input.text.length; i++) {
    const char = input.text[i];

    if (charIndexMap[char] !== undefined && charIndexMap[char] >= start) {
      start = charIndexMap[char] + 1;
    }

    maxLength = Math.max(maxLength, i - start + 1);
    charIndexMap[char] = i;
  }

  return maxLength;
}

// Check function to verify the correctness of the solution
function check() {
  assert.strictEqual(solve({"text": "abcabcbb"}), 3);
  assert.strictEqual(solve({"text": "aabbccddde"}), 4);
  assert.strictEqual(solve({"text": "bbbbb"}), 1);
  console.log("All test cases passed!");
}

check();
```

This solution defines a function `solve` that takes an object with a `text` property, then finds the length of the longest substring without any duplicate characters. It uses a map to keep track of the last index where each character was seen and updates the start point whenever it encounters a duplicate character. The check function tests the solution with various inputs to ensure its correctness.