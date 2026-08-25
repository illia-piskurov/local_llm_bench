export function solve(input) {
  const { a, b } = input;

  function isObject(v) {
    return v !== null && typeof v === 'object' && !Array.isArray(v);
  }

  function deepEqual(x, y) {
    if (x === y) return true;
    if (x === null || y === null) return x === y;
    const typeX = typeof x;
    const typeY = typeof y;
    if (typeX !== typeY) return false;

    if (Array.isArray(x)) {
      if (!Array.isArray(y)) return false;
      if (x.length !== y.length) return false;
      for (let i = 0; i < x.length; i++) {
        if (!deepEqual(x[i], y[i])) return false;
      }
      return true;
    }

    if (isObject(x)) {
      if (!isObject(y)) return false;
      const keysX = Object.keys(x);
      const keysY = Object.keys(y);
      if (keysX.length !== keysY.length) return false;
      for (const key of keysX) {
        if (!deepEqual(x[key], y[key])) return false;
      }
      return true;
    }

    // primitives (number, string, boolean, symbol, bigint)
    return x === y;
  }

  return deepEqual(a, b);
}