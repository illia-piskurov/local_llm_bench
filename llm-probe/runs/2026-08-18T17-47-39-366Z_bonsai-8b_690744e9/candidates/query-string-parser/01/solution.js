export function solve(input) {
  const query = input.query || '';
  if (query.startsWith('?')) {
    query = query.substring(1);
  }

  const pairs = query.split('&');
  const result = {};

  for (const pair of pairs) {
    const [key, value] = pair.split('=');

    if (!value) {
      value = true;
    } else {
      value = decodeURIComponent(value);
    }

    key = decodeURIComponent(key);

    if (key.endsWith('[]')) {
      const keyWithoutBrackets = key.slice(0, -2);
      const arr = result[keyWithoutBrackets] || [];
      arr.push(decodeURIComponent(value));
      result[keyWithoutBrackets] = arr;
    } else if (/[^\]]/.test(key)) {
      const nestedResult = result[key];
      if (!nestedResult) {
        nestedResult = {};
      }
      nestedResult[key] = value;
      result[key] = nestedResult;
    } else {
      // Handle nested brackets like 'user[address][city]'
      let current = result;
      const keys = key.split('[').filter(k => k !== '');
      for (let i = 0; i < keys.length; i++) {
        const nextKey = keys[i + 1].split(']')[0];
        if (!current[nextKey]) {
          current[nextKey] = {};
        }
        current = current[nextKey];
      }
      current[key] = value;
    }

    // Parse the value as number, boolean, or keep as string
    const decodedValue = decodeURIComponent(value);
    if (/^-?\d+$/.test(decodedValue)) {
      result[key] = parseInt(decodedValue, 10);
    } else if (['true', 'false'].includes(decodedValue.toLowerCase())) {
      result[key] = decodedValue.toLowerCase() === 'true';
    } else {
      result[key] = decodedValue;
    }
  }

  return result;
}