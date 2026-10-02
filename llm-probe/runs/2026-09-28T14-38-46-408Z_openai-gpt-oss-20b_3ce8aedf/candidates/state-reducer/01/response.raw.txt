export function solve(input) {
  // Deep clone the initial state to avoid mutation
  const result = JSON.parse(JSON.stringify(input.state));

  // Helper to navigate or create nested structure
  function setPath(obj, pathParts, value) {
    let cur = obj;
    for (let i = 0; i < pathParts.length - 1; i++) {
      const part = pathParts[i];
      if (cur[part] === undefined || typeof cur[part] !== 'object' || cur[part] === null) {
        cur[part] = {};
      }
      cur = cur[part];
    }
    cur[pathParts[pathParts.length - 1]] = value;
  }

  function getPath(obj, pathParts) {
    let cur = obj;
    for (const part of pathParts) {
      if (cur == null || typeof cur !== 'object') return undefined;
      cur = cur[part];
    }
    return cur;
  }

  function deletePath(obj, pathParts) {
    let cur = obj;
    for (let i = 0; i < pathParts.length - 1; i++) {
      const part = pathParts[i];
      if (cur[part] == null || typeof cur[part] !== 'object') return;
      cur = cur[part];
    }
    delete cur[pathParts[pathParts.length - 1]];
  }

  for (const action of input.actions) {
    const parts = action.path.split('.');
    switch (action.type) {
      case 'SET':
        setPath(result, parts, action.value);
        break;
      case 'TOGGLE': {
        const current = getPath(result, parts);
        const newVal = typeof current === 'boolean' ? !current : true;
        setPath(result, parts, newVal);
        break;
      }
      case 'ARRAY_PUSH': {
        let arr = getPath(result, parts);
        if (!Array.isArray(arr)) {
          setPath(result, parts, [action.item]);
        } else {
          // create new array to avoid mutation
          const newArr = arr.slice();
          newArr.push(action.item);
          setPath(result, parts, newArr);
        }
        break;
      }
      case 'ARRAY_REMOVE': {
        let arr = getPath(result, parts);
        if (Array.isArray(arr) && action.index >= 0 && action.index < arr.length) {
          const newArr = arr.slice(0, action.index).concat(arr.slice(action.index + 1));
          setPath(result, parts, newArr);
        }
        break;
      }
      case 'DELETE':
        deletePath(result, parts);
        break;
    }
  }

  return result;
}