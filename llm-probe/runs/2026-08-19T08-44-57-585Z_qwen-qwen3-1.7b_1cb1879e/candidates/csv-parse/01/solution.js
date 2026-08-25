export function solve(input) {
  if (!input || input.length === 0) return [];
  
  const lines = input.split('\n');
  const headers = lines[0].split(',');
  const result = [];

  for (let i = 1; i < lines.length; i++) {
    const row = lines[i];
    const values = row.split(',').map((val, idx) => {
      if (val.startsWith('"') && val.endsWith('"')) {
        return JSON.stringify(val.slice(1, -1));
      }
      return val;
    });

    const obj = {};
    for (let j = 0; j < headers.length; j++) {
      obj[headers[j]] = values[j];
    }
    result.push(obj);
  }

  return result;
}