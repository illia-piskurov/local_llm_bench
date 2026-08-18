export function solve(input) {
  const schema = input.schema;
  const data = input.data;
  const errors = {};
  
  for (const field in data) {
    if (!data.hasOwnProperty(field)) continue;
    
    const value = data[field];
    const rule = schema[field] || {};
    
    // Check required
    if (rule.required && (value === undefined || value === null)) {
      errors[field] = "Required";
      continue;
    }
    
    // Check type
    if (typeof value !== 'string' && typeof value !== 'number' && typeof value !== 'boolean') {
      errors[field] = "Invalid type";
      continue;
    }
    
    // Handle array types
    if (rule.type === 'array') {
      if (!Array.isArray(value)) {
        errors[field] = "Invalid type";
        continue;
      }
      
      const count = value.length;
      
      // Check min
      if (rule.min) {
        if (count < rule.min) {
          errors[field] = `Too few items`;
        } else if (count > rule.max && rule.max) {
          errors[field] = `Too many items`;
        }
      }
      
      // Check max
      if (rule.max) {
        if (count > rule.max) {
          errors[field] = `Too many items`;
        } else if (count < rule.min && rule.min) {
          errors[field] = `Too few items`;
        }
      }
      
      // Check pattern
      if (rule.pattern) {
        const regex = new RegExp(rule.pattern);
        if (!regex.test(value)) {
          errors[field] = "Invalid format";
        }
      } else if (typeof value === 'string' && rule.type !== 'array') {
        // For string type, check min and max
        if (rule.min) {
          if (value.length < rule.min) {
            errors[field] = "Too short";
          } else if (value.length > rule.max && rule.max) {
            errors[field] = "Too long";
          }
        }
        
        if (rule.max) {
          if (value.length > rule.max) {
            errors[field] = "Too large";
          } else if (value.length < rule.min && rule.min) {
            errors[field] = "Too small";
          }
        }
      } else if (typeof value === 'number' && rule.type !== 'array') {
        // For number type, check min and max
        if (rule.min && value < rule.min) {
          errors[field] = "Too small";
        } else if (rule.max && value > rule.max) {
          errors[field] = "Too large";
        }
      }
    }
  }
  
  return { valid: Object.keys(errors).length === 0, errors };
}