export function solve(input) {
  const schema = input.schema || {};
  const data = input.data || {};
  const errors = {};

  for (const field of Object.keys(schema)) {
    const rules = schema[field];
    const value = data[field];

    const fieldErrors = [];

    // required check
    if (rules.required) {
      if (value === undefined || value === null) {
        fieldErrors.push('Required');
        // skip other checks if missing
        errors[field] = fieldErrors;
        continue;
      }
    }

    // type check (if value is present)
    if (value !== undefined && value !== null) {
      let typeMatches = false;
      switch (rules.type) {
        case 'string':
          typeMatches = typeof value === 'string';
          break;
        case 'number':
          typeMatches = typeof value === 'number' && !Number.isNaN(value);
          break;
        case 'boolean':
          typeMatches = typeof value === 'boolean';
          break;
        case 'array':
          typeMatches = Array.isArray(value);
          break;
        default:
          typeMatches = false;
      }
      if (!typeMatches) {
        fieldErrors.push('Invalid type');
      } else {
        // min/max/pattern checks
        if (rules.type === 'string') {
          const len = value.length;
          if ('min' in rules && len < rules.min) fieldErrors.push('Too short');
          if ('max' in rules && len > rules.max) fieldErrors.push('Too long');
          if (rules.pattern !== undefined) {
            const re = new RegExp(rules.pattern);
            if (!re.test(value)) fieldErrors.push('Invalid format');
          }
        } else if (rules.type === 'number') {
          if ('min' in rules && value < rules.min) fieldErrors.push('Too small');
          if ('max' in rules && value > rules.max) fieldErrors.push('Too large');
        } else if (rules.type === 'array') {
          const len = value.length;
          if ('min' in rules && len < rules.min) fieldErrors.push('Too few items');
          if ('max' in rules && len > rules.max) fieldErrors.push('Too many items');
        }
      }
    }

    if (fieldErrors.length) {
      errors[field] = fieldErrors;
    }
  }

  const valid = Object.keys(errors).length === 0;
  return { valid, errors };
}