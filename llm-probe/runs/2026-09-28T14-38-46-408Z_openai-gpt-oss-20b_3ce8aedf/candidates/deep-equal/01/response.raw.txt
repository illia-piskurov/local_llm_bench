export function solve(input) {
  const { a, b } = input;
  return deepEqual(a, b);
}

function deepEqual(x, y) {
  if (x === y) return true;
  // handle null
  if (x == null || y == null) return x === y;
  const typeX = typeof x;
  const typeY = typeof y;
  if (typeX !== typeY) return false;

  // primitives
  if (typeX !== 'object') return x === y;

  const isArrayX = Array.isArray(x);
  const isArrayY = Array.isArray(y);

  if (isArrayX !== isArrayY) return false;

  if (isArrayX) {
    if (x.length !== y.length) return false;
    for (let i = 0; i < x.length; i++) {
      if (!deepEqual(x[i], y[i])) return false;
    }
    return true;
  }

  // plain objects
  const keysX = Object.keys(x);
  const keysY = Object.keys(y);
  if (keysX.length !== keysY.length) return false;
  for (const key of keysX) {
    if (!Object.prototype.hasOwnProperty.call(y, key)) return false;
    if (!deepEqual(x[key], y[key])) return false;
  }
  return true;
}