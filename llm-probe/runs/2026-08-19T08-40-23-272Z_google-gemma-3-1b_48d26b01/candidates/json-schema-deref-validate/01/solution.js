export function solve(input) {
  const schema = input.schema;
  const data = input.data;

  const valid = false;
  const errors = [];

  if (typeof data === 'object' && data !== null && typeof schema === 'object' && schema !== null) {
    if (data.definitions && data.definitions.hasOwnProperty('User')) {
      const user = data.definitions.User;
      if (user && typeof user.type === 'string') {
        if (!schema.properties.User.type || user.type !== schema.properties.User.type) {
          errors.push({path: '#/id', message: 'Expected type number'});
        }
      }
    }
  }

  return { valid, errors };
}