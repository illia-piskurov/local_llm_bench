export function solve(input) {
  const { state, actions } = input;

  // Helper function to create a deep copy of an object
  const cloneObject = (obj) => JSON.parse(JSON.stringify(obj));

  let currentState = cloneObject(state);

  actions.forEach(action => {
    switch (action.type) {
      case 'SET':
        setProperty(currentState, action.path, action.value);
        break;
      case 'TOGGLE':
        toggleProperty(currentState, action.path);
        break;
      case 'ARRAY_PUSH':
        arrayPush(currentState, action.path, action.item);
        break;
      case 'ARRAY_REMOVE':
        arrayRemove(currentState, action.path, action.index);
        break;
      case 'DELETE':
        deleteProperty(currentState, action.path);
        break;
    }
  });

  return currentState;
}

// Helper functions
function setProperty(obj, path, value) {
  const parts = path.split('.');
  let currentObj = obj;

  for (let i = 0; i < parts.length - 1; i++) {
    if (!currentObj[parts[i]]) {
      currentObj[parts[i]] = {};
    }
    currentObj = currentObj[parts[i]];
  }

  currentObj[parts[parts.length - 1]] = value;
}

function toggleProperty(obj, path) {
  const parts = path.split('.');
  let currentObj = obj;

  for (let i = 0; i < parts.length - 1; i++) {
    if (!currentObj[parts[i]]) {
      currentObj[parts[i]] = {};
    }
    currentObj = currentObj[parts[i]];
  }

  const key = parts[parts.length - 1];
  if (currentObj[key] !== undefined) {
    currentObj[key] = !currentObj[key];
  } else {
    currentObj[key] = true;
  }
}

function arrayPush(obj, path, item) {
  const parts = path.split('.');
  let currentObj = obj;

  for (let i = 0; i < parts.length - 1; i++) {
    if (!currentObj[parts[i]]) {
      currentObj[parts[i]] = {};
    }
    currentObj = currentObj[parts[i]];
  }

  const key = parts[parts.length - 1];
  if (!Array.isArray(currentObj[key])) {
    currentObj[key] = [item];
  } else {
    currentObj[key].push(item);
  }
}

function arrayRemove(obj, path, index) {
  const parts = path.split('.');
  let currentObj = obj;

  for (let i = 0; i < parts.length - 1; i++) {
    if (!currentObj[parts[i]]) {
      currentObj[parts[i]] = {};
    }
    currentObj = currentObj[parts[i]];
  }

  const key = parts[parts.length - 1];
  if (Array.isArray(currentObj[key]) && index >= 0 && index < currentObj[key].length) {
    currentObj[key].splice(index, 1);
  }
}

function deleteProperty(obj, path) {
  const parts = path.split('.');
  let currentObj = obj;

  for (let i = 0; i < parts.length - 1; i++) {
    if (!currentObj[parts[i]]) {
      return;
    }
    currentObj = currentObj[parts[i]];
  }

  delete currentObj[parts[parts.length - 1]];
}