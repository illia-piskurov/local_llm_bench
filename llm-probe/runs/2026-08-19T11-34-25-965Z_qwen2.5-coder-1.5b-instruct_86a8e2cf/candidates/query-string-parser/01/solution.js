export function solve(input) {
  const queryString = input.query ? input.query.slice(1) : '';
  const result = {};
  
  if (!queryString) return result;
  
  const pairs = queryString.split('&');
  for (const pair of pairs) {
    const [key, value] = pair.split('=').map(decodeURIComponent);
    
    if (value === '') {
      value = true; // Default to boolean true
    } else if (!isNaN(value)) {
      value = parseFloat(value); // Parse numeric values
    } else if (value.toLowerCase() === 'true') {
      value = true; // Parse boolean values
    } else if (value.toLowerCase() === 'false') {
      value = false; // Parse boolean values
    }
    
    const keyParts = key.split('[');
    if (keyParts.length > 1) {
      let currentObject = result;
      for (let i = 0; i < keyParts.length - 1; i++) {
        currentObject = currentObject[keyParts[i]];
        if (!currentObject) {
          currentObject = {};
          result[keyParts[i]] = currentObject;
        }
      }
      const nestedKey = keyParts.pop();
      currentObject[nestedKey] = value;
    } else {
      result[key] = value;
    }
  }
  
  return result;
}