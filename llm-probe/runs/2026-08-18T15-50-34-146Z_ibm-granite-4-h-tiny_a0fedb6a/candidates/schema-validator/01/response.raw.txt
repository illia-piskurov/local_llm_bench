export function solve(input) {
  const { schema, data } = input;
  const errors = {};

  for (const [field, fieldSchema] of Object.entries(schema)) {
    if (!data[field]) {
      if (fieldSchema.required) {
        if (!(errors[field] || (errors[field] = [])))
          errors[field] = ['Required'];
      }
      continue;
    }

    const value = data[field];
    const { type, min, max, pattern } = fieldSchema;

    switch (type) {
      case 'string':
        if (typeof value !== 'string') {
          errors[field] = ['Invalid type'];
          break;
        }
        if (pattern && !new RegExp(pattern).test(value)) {
          errors[field] = ['Invalid format'];
          break;
        }
        if (min != null && value.length < min) {
          if (!(errors[field] || (errors[field] = [])))
            errors[field] = ['Too short'];
        }
        if (max != null && value.length > max) {
          if (!(errors[field] || (errors[field] = [])))
            errors[field] = ['Too long'];
        }
        break;
      case 'number':
        if (typeof value !== 'number') {
          errors[field] = ['Invalid type'];
          break;
        }
        if (min != null && value < min) {
          if (!(errors[field] || (errors[field] = [])))
            errors[field] = ['Too small'];
        }
        if (max != null && value > max) {
          if (!(errors[field] || (errors[field] = [])))
            errors[field] = ['Too large'];
        }
        break;
      case 'boolean':
        if (typeof value !== 'boolean') {
          errors[field] = ['Invalid type'];
          break;
        }
        break;
      case 'array':
        if (!Array.isArray(value)) {
          errors[field] = ['Invalid type'];
          break;
        }
        if (min != null && value.length < min) {
          if (!(errors[field] || (errors[field] = [])))
            errors[field] = ['Too few items'];
        }
        if (max != null && value.length > max) {
          if (!(errors[field] || (errors[field] = [])))
            errors[field] = ['Too many items'];
        }
        break;
    }
  }

  return { valid: Object.keys(errors).length === 0, errors };
}