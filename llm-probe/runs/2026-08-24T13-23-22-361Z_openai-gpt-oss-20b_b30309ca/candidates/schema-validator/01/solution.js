export function solve(input) {
  const schema = input.schema || {};
  const data = input.data || {};

  const errors = {};

  for (const field in schema) {
    const rule = schema[field];
    const value = data[field];

    const fieldErrors = [];

    // Check required
    if (rule.required && (value === undefined || value === null)) {
      fieldErrors.push('Required');
    } else if (value !== undefined && value !== null) {
      // Type check
      let typeMatches = false;
      switch (rule.type) {
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
      }
      if (!typeMatches) {
        fieldErrors.push('Invalid type');
      } else {
        // Min / Max checks
        switch (rule.type) {
          case 'string': {
            const len = value.length;
            if (rule.min !== undefined && len < rule.min) {
              fieldErrors.push('Too short');
            }
            if (rule.max !== undefined && len > rule.max) {
              fieldErrors.push('Too long');
            }
            break;
          }
          case 'number': {
            const num = value;
            if (rule.min !== undefined && num < rule.min) {
              fieldErrors.push('Too small');
            }
            if (rule.max !== undefined && num > rule.max) {
              fieldErrors.push('Too large');
            }
            break;
          }
          case 'array': {
            const len = value.length;
            if (rule.min !== undefined && len < rule.min) {
              fieldErrors.push('Too few items');
            }
            if (rule.max !== undefined && len > rule.max) {
              fieldErrors.push('Too many items');
            }
            break;
          }
        }

        // Pattern for strings
        if (rule.type === 'string' && rule.pattern) {
          const regex = new RegExp(rule.pattern);
          if (!regex.test(value)) {
            fieldErrors.push('Invalid format');
          }
        }
      }
    }

    if (fieldErrors.length > 0) {
      errors[field] = fieldErrors;
    }
  }

  return { valid: Object.keys(errors).length === 0, errors };
}