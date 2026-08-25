export function solve(input) {
  const isDeepEqual = (a, b) => {
    if (typeof a !== 'object' || typeof b !== 'object') {
      return a === b;
    }
    if (a === null || b === null) return false;
    if (Array.isArray(a) && Array.isArray(b)) {
      if (a.length !== b.length) return false;
      for (let i = 0; i < a.length; i++) {
        if (!isDeepEqual(a[i], b[i])) return false;
      }
      return true;
    }
    if (Object.keys(a).length !== Object.keys(b).length) return false;
    const keysA = Object.keys(a);
    const keysB = Object.keys(b);
    for (const key of keysA) {
      if (!keysB.includes(key) || !isDeepEqual(a[key], b[key])) return false;
    }
    return true;
  };

  return isDeepEqual(input.a, input.b);
}