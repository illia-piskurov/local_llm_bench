export function solve(input) {
  const template = input.template;
  const data = input.data;
  return template.replace(/{{\s*([^}]+?)\s*}}/g, (_, expr) => {
    const parts = expr.split('.');
    let value = data;
    for (const part of parts) {
      if (value == null || typeof value !== 'object' && typeof value !== 'function') {
        value = undefined;
        break;
      }
      if (Array.isArray(value) && !isNaN(part)) {
        value = value[Number(part)];
      } else {
        value = value[part];
      }
    }
    if (value === undefined || value === null) return '';
    return String(value);
  });
}