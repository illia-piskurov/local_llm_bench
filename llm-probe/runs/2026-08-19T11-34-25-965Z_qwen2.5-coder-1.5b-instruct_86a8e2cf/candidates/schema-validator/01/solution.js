export function solve(input) {
  const { schema, data } = input;
  
  if (typeof schema !== 'object' || schema === null) return { valid: false };
  
  let errors = {};
  
  for (const [field, rule] of Object.entries(schema)) {
    if (rule.required && (!data[field] || data[field] === null)) {
      errors[field] = ['Required'];
      continue;
    }
    
    const value = data[field];
    
    switch (rule.type) {
      case 'string':
        if (!value || typeof value !== 'string') {
          errors[field] = ['Invalid type'];
          break;
        }
        
        if (typeof rule.min === 'number' && value.length < rule.min) {
          errors[field].push('Too short');
        } else if (typeof rule.max === 'number' && value.length > rule.max) {
          errors[field].push('Too long');
        } else if (typeof rule.pattern !== 'undefined' && !new RegExp(rule.pattern).test(value)) {
          errors[field].push('Invalid format');
        }
        break;
      case 'number':
        if (!value || typeof value !== 'number') {
          errors[field] = ['Invalid type'];
          break;
        }
        
        if (typeof rule.min === 'number' && value < rule.min) {
          errors[field].push('Too small');
        } else if (typeof rule.max === 'number' && value > rule.max) {
          errors[field].push('Too large');
        }
        break;
      case 'boolean':
        if (!value || typeof value !== 'boolean') {
          errors[field] = ['Invalid type'];
          break;
        }
        break;
      case 'array':
        if (!value || !Array.isArray(value)) {
          errors[field] = ['Invalid type'];
          break;
        }
        
        if (typeof rule.min === 'number' && value.length < rule.min) {
          errors[field].push('Too few items');
        } else if (typeof rule.max === 'number' && value.length > rule.max) {
          errors[field].push('Too many items');
        }
        break;
    }
  }
  
  return { valid: Object.keys(errors).length === 0, errors };
}