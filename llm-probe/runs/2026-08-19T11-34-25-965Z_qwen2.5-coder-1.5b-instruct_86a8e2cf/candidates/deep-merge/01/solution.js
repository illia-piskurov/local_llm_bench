export function solve(input) {
  if (!input.objects.length) return {};

  const mergedObject = {};
  
  input.objects.forEach(obj => {
    for (const key in obj) {
      if (obj[key] !== undefined) {
        if (typeof obj[key] === 'object' && !Array.isArray(obj[key])) {
          // Recursively merge objects
          mergedObject[key] = solve({ objects: [obj[key]] });
        } else if (Array.isArray(obj[key])) {
          // Replace array with the later value
          mergedObject[key] = obj[key];
        } else {
          // Replace primitive values
          mergedObject[key] = obj[key];
        }
      }
    }
  });

  return mergedObject;
}