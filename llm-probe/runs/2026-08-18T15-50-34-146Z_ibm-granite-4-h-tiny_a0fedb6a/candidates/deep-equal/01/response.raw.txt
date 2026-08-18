export function solve(input) {
  return deepEqual(input.a, input.b);
}

function deepEqual(a, b) {
  if (a === null && b === null) return true;
  if (a === undefined || b === undefined) return false;
  if (typeof a !== typeof b) return false;

  const type = typeof a;
  if (type !== 'object' && !Array.isArray(a)) return a === b;

  if (Array.isArray(a)) {
    if (!Array.isArray(b) || a.length !== b.length) return false;
    for (let i = 0; i < a.length; i++) {
      if (!deepEqual(a[i], b[i])) return false;
    }
    return true;
  }

  const keysA = Object.keys(a);
  const keysB = Object.keys(b);

  if (keysA.length !== keysB.length) return false;

  for (const key of keysA) {
    if (!keysB.includes(key) || !deepEqual(a[key], b[key])) return false;
  }

  return true;
}