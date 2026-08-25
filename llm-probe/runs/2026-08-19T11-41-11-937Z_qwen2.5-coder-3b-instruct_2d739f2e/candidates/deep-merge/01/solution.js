export function solve(input) {
  if (input.objects.length === 0) {
    return {};
  }

  const initialObject = input.objects[0];
  let mergedObject = { ...initialObject };

  for (let i = 1; i < input.objects.length; i++) {
    const currentObject = input.objects[i];

    for (const key in currentObject) {
      if (currentObject[key] !== undefined) {
        if (typeof currentObject[key] === 'object' && !Array.isArray(currentObject[key])) {
          mergedObject[key] = solve({ objects: [mergedObject[key], currentObject[key]] });
        } else {
          mergedObject[key] = currentObject[key];
        }
      }
    }
  }

  return mergedObject;
}