export function solve(input) {
  const objects = Array.isArray(input.objects) ? input.objects : [];
  if (!objects.length) return {};

  const isPlainObject = (obj) =>
    typeof obj === 'object' && obj !== null && !Array.isArray(obj);

  const mergeValues = (target, source) => {
    if (isPlainObject(source)) {
      if (!isPlainObject(target)) target = {};
      for (const key in source) {
        const srcVal = source[key];
        if (srcVal === undefined) continue;
        target[key] = mergeValues(target[key], srcVal);
      }
    } else {
      // arrays or primitives replace
      target = source;
    }
    return target;
  };

  let result = {};
  for (const obj of objects) {
    if (!isPlainObject(obj)) continue;
    result = mergeValues(result, obj);
  }
  return result;
}