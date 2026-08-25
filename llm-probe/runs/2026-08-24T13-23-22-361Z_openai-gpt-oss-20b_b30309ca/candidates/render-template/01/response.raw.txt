export function solve(input) {
  const { template, data } = input;
  // Regular expression to match {{ ... }} with optional whitespace
  const regex = /\{\{\s*([^}]+?)\s*\}\}/g;

  return template.replace(regex, (_, pathStr) => {
    const parts = pathStr.split('.').map(p => p.trim());
    let value = data;
    for (const key of parts) {
      if (value == null || typeof value !== 'object' && !Array.isArray(value)) {
        value = undefined;
        break;
      }
      value = value[key];
      if (value === undefined) break;
    }
    if (value === undefined || value === null) return '';
    // Convert non-string primitives to string
    return typeof value !== 'string' ? String(value) : value;
  });
}