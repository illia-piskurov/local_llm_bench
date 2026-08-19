export function solve(input) {
  let valid = true;
  let errors = {};

  for (const field in input.schema) {
    if (input.schema[field].type === 'string') {
      if (!input.data[field] || typeof input.data[field] !== 'string') {
        errors[field] = "Invalid data type";
      }
    } else if (input.schema[field].type === 'number') {
      if (input.data[field] === undefined || input.data[field] === null) {
        errors[field] = "Required";
      }
    } else if (input.schema[field].type === 'boolean') {
      if (!input.data[field]) {
        errors[field] = "Required";
      }
    } else if (input.schema[field].type === 'array') {
      if (input.data[field] && !Array.isArray(input.data[field])) {
        errors[field] = "Too many items";
      }
    } else if (input.schema[field].pattern === 'Invalid format') {
      errors[field] = "Invalid format";
    }
  }

  return { valid, errors };
}