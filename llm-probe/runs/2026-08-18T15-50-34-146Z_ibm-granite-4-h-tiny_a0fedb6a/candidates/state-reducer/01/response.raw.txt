export function solve(input) {
  const { state, actions } = input;
  let result = JSON.parse(JSON.stringify(state));
  
  for (const action of actions) {
    if (action.type === 'SET') {
      let obj = result;
      const pathParts = action.path.split('.');
      for (let i = 0; i < pathParts.length - 1; i++) {
        const part = pathParts[i];
        if (!obj[part]) {
          obj[part] = {};
        }
        obj = obj[part];
      }
      obj[pathParts[pathParts.length - 1]] = action.value;
    } else if (action.type === 'TOGGLE') {
      let obj = result;
      const pathParts = action.path.split('.');
      for (let i = 0; i < pathParts.length - 1; i++) {
        const part = pathParts[i];
        obj = obj[part];
      }
      const toggleKey = pathParts[pathParts.length - 1];
      if (typeof obj[toggleKey] === 'boolean') {
        obj[toggleKey] = !obj[toggleKey];
      } else {
        obj[toggleKey] = true;
      }
    } else if (action.type === 'ARRAY_PUSH') {
      let arr = result;
      const pathParts = action.path.split('.');
      for (let i = 0; i < pathParts.length - 1; i++) {
        const part = pathParts[i];
        if (!arr[part]) {
          arr[part] = [];
        }
        arr = arr[part];
      }
      arr.push(action.item);
    } else if (action.type === 'ARRAY_REMOVE') {
      let arr = result;
      const pathParts = action.path.split('.');
      for (let i = 0; i < pathParts.length - 1; i++) {
        const part = pathParts[i];
        arr = arr[part];
      }
      const index = action.index;
      if (index >= 0 && index < arr.length) {
        arr.splice(index, 1);
      }
    } else if (action.type === 'DELETE') {
      let obj = result;
      const pathParts = action.path.split('.');
      for (let i = 0; i < pathParts.length - 1; i++) {
        const part = pathParts[i];
        obj = obj[part];
      }
      delete obj[pathParts[pathParts.length - 1]];
    }
  }
  
  return result;
}