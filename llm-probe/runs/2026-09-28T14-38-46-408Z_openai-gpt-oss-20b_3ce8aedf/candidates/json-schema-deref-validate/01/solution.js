export function solve(input) {
  const { definitions, schema: rootSchema, data } = input;
  const errors = [];

  function resolve(schema) {
    if (schema.$ref && typeof schema.$ref === 'string') {
      const ref = schema.$ref;
      if (!ref.startsWith('#/definitions/')) return schema;
      const parts = ref.slice(14).split('/');
      let target = definitions;
      for (const part of parts) {
        if (target && typeof target === 'object' && part in target) {
          target = target[part];
        } else {
          return schema;
        }
      }
      return target || schema;
    }
    return schema;
  }

  function validate(value, schema, path) {
    const s = resolve(schema);
    if (!s || typeof s !== 'object') return;

    // Type validation
    const type = s.type;
    if (type) {
      switch (type) {
        case 'string':
          if (typeof value !== 'string') {
            errors.push({ path, message: 'Expected type string' });
            return;
          }
          if (s.minLength !== undefined && value.length < s.minLength) {
            errors.push({ path, message: 'String length less than minLength' });
          }
          break;
        case 'number':
          if (typeof value !== 'number') {
            errors.push({ path, message: 'Expected type number' });
          }
          break;
        case 'boolean':
          if (typeof value !== 'boolean') {
            errors.push({ path, message: 'Expected type boolean' });
          }
          break;
        case 'array':
          if (!Array.isArray(value)) {
            errors.push({ path, message: 'Expected type array' });
          } else {
            if (s.minItems !== undefined && value.length < s.minItems) {
              errors.push({ path, message: 'Array length less than minItems' });
            }
            if (s.items) {
              for (let i = 0; i < value.length; i++) {
                validate(value[i], s.items, `${path}/items/${i}`);
              }
            }
          }
          break;
        case 'object':
          if (typeof value !== 'object' || value === null || Array.isArray(value)) {
            errors.push({ path, message: 'Expected type object' });
          } else {
            const props = s.properties || {};
            // Required
            if (Array.isArray(s.required)) {
              for (const req of s.required) {
                if (!(req in value)) {
                  errors.push({ path: `${path}/${req}`, message: 'Missing required property' });
                }
              }
            }
            // Properties
            for (const key of Object.keys(props)) {
              if (key in value) {
                validate(value[key], props[key], `${path}/${key}`);
              }
            }
            // Additional properties
            if (s.additionalProperties === false) {
              for (const key of Object.keys(value)) {
                if (!(key in props)) {
                  errors.push({ path: `${path}/${key}`, message: 'Additional property not allowed' });
                }
              }
            }
          }
          break;
      }
    }

    // Enum validation
    if (Array.isArray(s.enum)) {
      const found = s.enum.some((v) => Object.is(v, value));
      if (!found) {
        errors.push({ path, message: 'Value not in enum' });
      }
    }
  }

  validate(data, rootSchema, '#');

  return { valid: errors.length === 0, errors };
}