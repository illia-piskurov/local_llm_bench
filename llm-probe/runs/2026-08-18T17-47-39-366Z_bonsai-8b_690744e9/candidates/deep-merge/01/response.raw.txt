export function solve(input) {
  if (!input || input.objects.length === 0) return {};

  const result = { ...input.objects[0] };

  for (let i = 1; i < input.objects.length; i++) {
    const obj = input.objects[i];
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        if (typeof result[key] === 'object' && !Array.isArray(result[key])) {
          // Recursive merge
          if (result[key] && typeof result[key] === 'object') {
            result[key] = { ...result[key], ...obj[key] };
          }
        } else {
          // Replace with later value
          result[key] = obj[key];
        }
      }
    }
  }

  return result;
}