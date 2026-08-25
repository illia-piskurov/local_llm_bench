export function solve(input) {
  const query = input.query.replace(/^(\?|#|&)/, '');
  if (!query) return {};
  
  const result = {};
  for (const pair of query.split('&')) {
    let [key, value] = pair.split('=');
    
    if (value === undefined) {
      value = true;
    } else {
      try { 
        value = Number(value);
        if (Number.isFinite(value)) continue;
      } catch (_) {}
      
      value = value.toLowerCase() === 'true' ? true :
              value.toLowerCase() === 'false' ? false : value;
    }
    
    key = decodeURIComponent(key);
    
    while (key.includes('[') && key.includes(']')) {
      const parts = key.slice(1, -1).split(/(?<!\\)\]/);
      key = parts[0];
      
      if (!result[key]) result[key] = {};
      if (!Array.isArray(result[key])) result[key] = [result[key]];
      result = result[key];
      key = parts.pop();
    }
    
    const keys = key.split(/\]\[/).map(part => part.replace(/[\[\]]/g, ''));
    let current = result;
    
    for (let i = 0; i < keys.length - 1; i++) {
      if (!current[keys[i]]) current[keys[i]] = {};
      current = current[keys[i]];
    }
    
    const lastKey = keys[keys.length - 1];
    
    if (Array.isArray(current[lastKey])) {
      current[lastKey].push(value);
    } else {
      current[lastKey] = value;
    }
  }
  
  return result;
}