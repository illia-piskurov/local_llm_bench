export function solve(input) {
  if (!Array.isArray(input.objects)) return {};

  const merged = {};

  for (const obj of input.objects) {
    for (const [key, value] of Object.entries(obj)) {
      if (value === undefined || value === null) continue; // ignore keys with no value

      if (typeof key === 'string') {
        // Primitive types: replace entirely with later value
        const type = typeof value;
        merged[key] = type === 'object' ? mergeObjects(value) : value;
      } else if (Array.isArray(key)) {
        // Nested object keys that are arrays (e.g. "colors.primary")
        const subKey = key[0];
        let nestedValue;

        if (type === 'object') {
          nestedValue = mergeObjects(value);
        } else {
          nestedValue = value;
        }

        merged[key] = type === 'object' ? nestedValue : nestedValue;
      } else {
        // Array keys or primitives: replace entirely
        merged[key] = value;
      }
    }
  }

  return Object.fromEntries(Object.entries(merged));
}

function mergeObjects(obj1, obj2) {
  if (obj2 === undefined || obj2 === null) return obj1;

  const result = {};

  for (const [key, value] of Object.entries(obj1)) {
    // If key is an array (e.g. "colors.primary")
    if (typeof key === 'string' && Array.isArray(key[0])) {
      const subKey = key[0];
      let nestedValue;

      if (typeof value === 'object') {
        nestedValue = mergeObjects(value);
      } else {
        nestedValue = value;
      }

      result[key] = nestedValue;
    } else {
      // Object with primitive key: check if value is an array or object
      const type = typeof obj2[key];
      if (type === 'object') {
        result[key] = mergeObjects(obj1[key], obj2[key]);
      } else if (!Array.isArray(value)) {
        result[key] = value;
      } else {
        // Array value: replace with later object's array, or primitive
        const arrKey = Object.keys(obj2);
        let finalArrValue = null;

        for (const arrKey of arrKey) {
          if (typeof obj2[arrKey] === 'object') {
            finalArrValue = mergeObjects(obj1[arrKey], obj2[arrKey]);
          } else if (!Array.isArray(value)) {
            finalArrValue = value;
          }
        }

        result[key] = finalArrValue;
      }
    }
  }

  // Handle array keys (e.g., "colors.primary" is a primitive key but represents an array)
  if (typeof result === 'object' && Array.isArray(Object.keys(result))) {
    const arrKey = Object.keys(result)[0];
    let finalArrValue;
    for (const arrKey of Object.keys(obj2)) {
      if (result[Object.keys(result).indexOf(arrKey)] !== undefined) {
        result[arrKey] = mergeObjects(result[arrKey], obj2[arrKey]);
      } else if (!Array.isArray(value)) {
        finalArrValue = value;
      } else {
        finalArrValue = Array.from(Object.values(obj1));
      }
    }

    // If the array key was "colors.primary" (primitive), merge its values from obj2's keys
    if (arrKey === 'primary' || arrKey === 'secondary') {
      const keysWithValues = Object.keys(obj2).filter(k => typeof result[k] !== 'object');
      for (const k of keysWithValues) {
        finalArrValue = [...finalArrValue, ...Object.values(obj2[k])];
      }

      // Remove the key from result since we've merged it into arrKey
      const keysToRemove = Object.keys(result).filter(k => k === arrKey);
      for (const k of keysToRemove) {
        delete result[k];
      }
    } else {
      result[arrKey] = finalArrValue;
    }
  }

  return result;
}