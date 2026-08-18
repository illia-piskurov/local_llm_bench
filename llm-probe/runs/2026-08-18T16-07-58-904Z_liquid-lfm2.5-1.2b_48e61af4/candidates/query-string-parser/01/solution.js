export function solve(input) {
  const query = input.query || '';
  if (query.trim() === '') return {};

  const decoder = (value) => {
    if (value === null || value === undefined) return '';
    let decoded = value.replace(/&/g, '&').replace(/"/g, '&');
    if (decoded.startsWith('decodeURI')) return decodeURIComponent(decoded);
    if (decoded.match(/^([^&=]+)=(.*)$/)) {
      const [key, val] = decoded.split('=', 2);
      key = key.replace(/^\./, '');
      val = decoder(val);
      return key === '[]' ? [] : new Map(val.split(',').map(v => [v.trim(), decoder(v)]));
    }
    return decoder(value);
  };

  const parsed = {};
  let i = 0;
  while (i < query.length) {
    const char = query[i];
    if (char === '?') i++;
    else if (char === '&') {
      const start = i;
      while (i < query.length && query[i] !== '&') i++;
      const key = decoder(query.slice(start, i));
      const valuePart = query.slice(i + 1);
      let value = '';
      if (valuePart.startsWith('[') && valuePart.endsWith(']')) {
        const inner = valuePart.substring(1, valuePart.length - 1);
        let nested = {};
        let j = 0;
        while (j < inner.length && inner[j] !== ']') {
          if (inner[j] === '[') nested = { ...nested, ...parse(key, parsed) };
          else nested = { ...nested, [inner[j + 1]] = parseValue(inner[j + 1], parsed) };
          j++;
        }
        value = nested;
      } else {
        value = valuePart;
      }
      parsed[key] = value ? parseValue(value, parsed) : true;
      i++;
    }
  }
  return parsed;
}

function parseValue(value, obj) {
  const num = value.replace(/^\d+/, '').trim();
  if (!isNaN(num)) return Number(num);
  if (num === 'true' || num === 'false') return obj[value];
  return obj[value] ? obj[value] : null;
}