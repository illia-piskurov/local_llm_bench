export function solve(input) {
  const query = input.query.startsWith('?') ? input.query.slice(1) : input.query;
  if (!query) return {};

  const result = {};
  for (const part of query.split('&')) {
    const [key, value] = part.split('=');
    let decodedKey = decodeURIComponent(key);

    if (decodedKey.endsWith('[]')) {
      const keyWithoutBracket = decodedKey.slice(0, -2);
      if (!result[keyWithoutBracket]) result[keyWithoutBracket] = [];
      result[keyWithoutBracket].push(value ? decodeURIComponent(value) : true);
    } else if (key.includes('[')) {
      let currentObj = result;
      const nestedKeys = decodedKey.split(/\[\]/g).map((k, i) => k.trim());
      for (let i = 0; i < nestedKeys.length; i++) {
        if (!currentObj[nestedKeys[i]]) {
          currentObj[nestedKeys[i]] = {};
        }
        currentObj = currentObj[nestedKeys[i]];
      }
      currentObj[nestedKeys.pop()] = value ? decodeURIComponent(value) : true;
    } else {
      result[decodedKey] = value ? decodeURIComponent(value) : true;
    }
  }

  return result;
}