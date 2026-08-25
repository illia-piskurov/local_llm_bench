export function solve(input) {
  if (!input || input === '') return [];

  const lines = input.split('\n');
  if (lines.length < 2) return [];

  const header = lines[0].split(',');

  const data = lines.slice(1).map(line => {
    const obj = {};
    line.split(',').forEach((value, index) => {
      if (value.includes('"')) {
        value = value.replace(/"/g, '');
      } else {
        value = value.trim();
      }
      obj[header[index]] = value;
    });
    return obj;
  });

  return data;
}