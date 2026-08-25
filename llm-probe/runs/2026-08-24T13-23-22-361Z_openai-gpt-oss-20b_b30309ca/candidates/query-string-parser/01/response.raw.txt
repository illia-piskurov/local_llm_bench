export function solve(input) {
  const query = input.query ?? '';
  const trimmed = query.startsWith('?') ? query.slice(1) : query;
  if (!trimmed) return {};

  const result = {};

  const pairs = trimmed.split('&');
  for (const pair of pairs) {
    if (!pair) continue;
    let [rawKey, rawValue] = pair.includes('=')
      ? pair.split('=', 2)
      : [pair, true];
    const key = decodeURIComponent(rawKey);
    const value =
      typeof rawValue === 'boolean'
        ? true
        : parseValue(decodeURIComponent(rawValue));

    if (key.endsWith('[]')) {
      const base = key.slice(0, -2);
      if (!Array.isArray(result[base])) result[base] = [];
      result[base].push(value);
      continue;
    }

    const path = key.split(/\[|\]/).filter(Boolean);
    setPath(result, path, value);
  }

  return result;

  function parseValue(v) {
    if (v === 'true') return true;
    if (v === 'false') return false;
    const num = Number(v);
    if (!Number.isNaN(num) && Number.isFinite(num)) return num;
    return v;
  }

  function setPath(obj, path, val) {
    let current = obj;
    for (let i = 0; i < path.length; i++) {
      const part = path[i];
      if (i === path.length - 1) {
        if (
          typeof current[part] === 'object' &&
          current[part] !== null &&
          !Array.isArray(current[part])
        ) {
          current[part] = val;
        } else {
          current[part] = val;
        }
      } else {
        if (!Object.prototype.hasOwnProperty.call(current, part) || typeof current[part] !== 'object' || current[part] === null) {
          current[part] = {};
        }
        current = current[part];
      }
    }
  }
}