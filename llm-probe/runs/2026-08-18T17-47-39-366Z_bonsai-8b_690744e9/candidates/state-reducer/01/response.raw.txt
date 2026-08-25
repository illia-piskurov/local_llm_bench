export function solve(input) {
  const { state, actions } = input;
  const newState = { ...state };

  for (const action of actions) {
    if (action.type === 'SET') {
      const paths = action.path.split('.');
      let current = newState;
      for (let i = 0; i < paths.length; i++) {
        const key = paths[i];
        if (current[key] === undefined) {
          current[key] = {};
        }
        current = current[key];
      }
      current['value'] = action.value;
    } else if (action.type === 'TOGGLE') {
      const path = action.path;
      let current = newState;
      for (let i = 0; i < paths.length; i++) {
        const key = paths[i];
        if (current[key] === undefined) {
          current[key] = false;
        }
        current = current[key];
      }
      current['value'] = !current['value'];
    } else if (action.type === 'ARRAY_PUSH') {
      const path = action.path;
      const item = action.item;
      let current = newState;
      for (let i = 0; i < paths.length; i++) {
        const key = paths[i];
        if (current[key] === undefined) {
          current[key] = [];
        }
        current = current[key];
      }
      current['value'].push(item);
    } else if (action.type === 'ARRAY_REMOVE') {
      const path = action.path;
      const index = action.index;
      let current = newState;
      for (let i = 0; i < paths.length; i++) {
        const key = paths[i];
        if (current[key] === undefined) {
          current[key] = [];
        }
        current = current[key];
      }
      if (index >= 0 && index < current['value'].length) {
        current['value'].splice(index, 1);
      }
    } else if (action.type === 'DELETE') {
      const path = action.path;
      let current = newState;
      for (let i = 0; i < paths.length; i++) {
        const key = paths[i];
        if (current[key] === undefined) {
          delete current;
          break;
        }
        current = current[key];
      }
    }
  }

  return JSON.stringify(newState, null, 2);
}