export function solve(input) {
  const a = input.a;
  const b = input.b;

  // Helper function for deep equality check
  function isEqual(val1, val2) {
    // 1. Strict equality check (handles primitives, same references, and both null/undefined if they are equal)
    if (val1 === val2) return true;

    // 2. If either is null or not an object, they must be unequal if step 1 failed.
    if (val1 === null || typeof val1 !== 'object' || val2 === null || typeof val2 !== 'object') {
      return false;
    }

    // 3. Handle Arrays
    const isArray1 = Array.isArray(val1);
    const isArray2 = Array.isArray(val2);

    if (isArray1 !== isArray2) {
      return false; // One is array, the other is object
    }

    if (isArray1) { // Both are arrays
      if (val1.length !== val2.length) return false;
      for (let i = 0; i < val1.length; i++) {
        if (!isEqual(val1[i], val2[i])) return false;
      }
      return true;
    } else { // Both are plain objects
      const keys1 = Object.keys(val1);
      const keys2 = Object.keys(val2);

      if (keys1.length !== keys2.length) return false;

      for (const key of keys1) {
        // Check if val2 has the key AND recursively check the value
        if (!Object.prototype.hasOwnProperty.call(val2, key) || !isEqual(val1[key], val2[key])) {
          return false;
        }
      }
      return true;
    }
  }

  return isEqual(a, b);
}