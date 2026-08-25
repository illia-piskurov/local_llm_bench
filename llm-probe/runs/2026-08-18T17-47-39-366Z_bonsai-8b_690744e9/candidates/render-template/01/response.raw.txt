export function solve(input) {
  const { template } = input;
  const { data } = input;

  const replace = (str, path) => {
    const parts = path.split('.');
    let value = data;

    for (let i = 0; i < parts.length; i++) {
      const key = parts[i];
      if (value === undefined || value === null) {
        return '';
      }
      if (typeof value !== 'object' || value === null) {
        return '';
      }
      if (Array.isArray(value)) {
        if (i >= value.length) {
          return '';
        }
        value = value[i];
      } else {
        value = value[key] || '';
      }
    }

    return String(value);
  };

  return template.replace(/\{\{([^\}]+)\}\}/g, (match, key) => {
    const path = key;
    const value = replace(match, path);
    return value;
  });
}