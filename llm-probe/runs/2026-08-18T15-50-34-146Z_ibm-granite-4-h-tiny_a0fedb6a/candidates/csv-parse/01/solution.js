export function solve(input) {
  if (!input.trim()) return [];
  const lines = input.split(/\\r?\\n/).filter(line => line.trim());
  const headers = lines[0].split(',').map(header => header.trim());
  const parseValue = (value) => {
    if (/^"/.test(value)) {
      value = value.replace(/^"|"$/g, '');
      value = value.replace(/""/g, '"');
    }
    return value.trim();
  };
  return lines.slice(1).map(line => {
    const values = line.split(',');
    return headers.reduce((obj, header, index) => {
      obj[header] = parseValue(values[index]);
      return obj;
    }, {});
  });
}