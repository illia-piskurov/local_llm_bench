export function solve(input) {
  const { state, actions } = input;
  // deep clone initial state
  const clone = JSON.parse(JSON.stringify(state));

  // helper to get or create nested object along path
  const traverse = (obj, parts, createMissing = false) => {
    let current = obj;
    for (let i = 0; i < parts.length - 1; i++) {
      const part = parts[i];
      if (!(part in current) || typeof current[part] !== 'object' || current[part] === null) {
        if (createMissing) current[part] = {};
        else return undefined;
      }
      current = current[part];
    }
    return { parent: current, key: parts[parts.length - 1] };
  };

  actions.forEach(action => {
    const pathParts = action.path.split('.');
    switch (action.type) {
      case 'SET': {
        const target = traverse(clone, pathParts, true);
        if (target) target.parent[target.key] = action.value;
        break;
      }
      case 'TOGGLE': {
        const target = traverse(clone, pathParts);
        if (target) {
          const val = target.parent[target.key];
          target.parent[target.key] = typeof val === 'boolean' ? !val : true;
        }
        break;
      }
      case 'ARRAY_PUSH': {
        const target = traverse(clone, pathParts, true);
        if (target) {
          let arr = target.parent[target.key];
          if (!Array.isArray(arr)) arr = [];
          arr.push(action.item);
          target.parent[target.key] = arr;
        }
        break;
      }
      case 'ARRAY_REMOVE': {
        const target = traverse(clone, pathParts);
        if (target) {
          const arr = target.parent[target.key];
          if (Array.isArray(arr) && action.index >= 0 && action.index < arr.length) {
            arr.splice(action.index, 1);
          }
        }
        break;
      }
      case 'DELETE': {
        const target = traverse(clone, pathParts);
        if (target) delete target.parent[target.key];
        break;
      }
    }
  });

  return clone;
}