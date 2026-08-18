export function solve(input) {
  if (!input.objects || input.objects.length === 0) return {};

  const result = {};
  input.objects.forEach(obj => {
    result = mergeObjects(result, obj);
  });
  return result;
}

function mergeObjects(target, source) {
  for (const key in source) {
    if (source[key] !== undefined) {
      if (typeof target[key] === 'object' && typeof source[key] === 'object') {
        target[key] = mergeObjects(target[key], source[key]);
      } else {
        target[key] = source[key];
      }
    }
  }
}