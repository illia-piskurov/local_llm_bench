export function solve(input) {
  const lines = input.split('\n').filter(line => line.trim() !== '');
  if (lines.length === 0 || lines[0].trim() === '') return [];

  const headers = lines[0].split(',');
  const result = [];

  for (let i = 1; i < lines.length; i++) {
    const row = [];
    let value = '';
    let inQuote = false;

    for (let j = 0; j < headers.length; j++) {
      if (lines[i][j] === '"') {
        inQuote = !inQuote;
        value += lines[i][j];
        continue;
      }

      if (inQuote) {
        row.push(value);
        value = '';
        continue;
      }

      const commaIndex = lines[i].indexOf(',');
      if (commaIndex !== -1) {
        row.push(lines[i].trim());
        value = '';
      } else {
        row.push(lines[i].trim());
      }
    }

    if (row.length === headers.length) {
      result.push({ [headers[k]]: row[k] for k in headers });
    }
  }

  return result;
}