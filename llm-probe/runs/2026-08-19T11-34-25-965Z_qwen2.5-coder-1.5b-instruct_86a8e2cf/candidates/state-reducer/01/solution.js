export function solve(input) {
    let state = input.state;
    for (const action of input.actions) {
        switch (action.type) {
            case 'SET':
                const pathComponents = action.path.split('.');
                let currentPath = state;
                for (let i = 0; i < pathComponents.length - 1; i++) {
                    if (!currentPath.hasOwnProperty(pathComponents[i])) {
                        currentPath[pathComponents[i]] = {};
                    }
                    currentPath = currentPath[pathComponents[i]];
                }
                currentPath[pathComponents[pathComponents.length - 1]] = action.value;
                break;
            case 'TOGGLE':
                const pathComponents = action.path.split('.');
                let currentPath = state;
                for (let i = 0; i < pathComponents.length - 1; i++) {
                    if (!currentPath.hasOwnProperty(pathComponents[i])) {
                        currentPath[pathComponents[i]] = {};
                    }
                    currentPath = currentPath[pathComponents[i]];
                }
                const value = currentPath[pathComponents[pathComponents.length - 1]];
                currentPath[pathComponents[pathComponents.length - 1]] = typeof value === 'boolean' ? !value : true;
                break;
            case 'ARRAY_PUSH':
                const pathComponents = action.path.split('.');
                let currentPath = state;
                for (let i = 0; i < pathComponents.length - 2; i++) {
                    if (!currentPath.hasOwnProperty(pathComponents[i])) {
                        currentPath[pathComponents[i]] = {};
                    }
                    currentPath = currentPath[pathComponents[i]];
                }
                const arrayPath = pathComponents[pathComponents.length - 1];
                if (!Array.isArray(currentPath[arrayPath])) {
                    currentPath[arrayPath] = [];
                }
                currentPath[arrayPath].push(action.item);
                break;
            case 'ARRAY_REMOVE':
                const pathComponents = action.path.split('.');
                let currentPath = state;
                for (let i = 0; i < pathComponents.length - 2; i++) {
                    if (!currentPath.hasOwnProperty(pathComponents[i])) {
                        currentPath[pathComponents[i]] = {};
                    }
                    currentPath = currentPath[pathComponents[i]];
                }
                const arrayPath = pathComponents[pathComponents.length - 1];
                if (Array.isArray(currentPath[arrayPath]) && action.index >= 0 && action.index < currentPath[arrayPath].length) {
                    currentPath[arrayPath].splice(action.index, 1);
                }
                break;
            case 'DELETE':
                const pathComponents = action.path.split('.');
                let currentPath = state;
                for (let i = 0; i < pathComponents.length - 1; i++) {
                    if (!currentPath.hasOwnProperty(pathComponents[i])) {
                        currentPath[pathComponents[i]] = {};
                    }
                    currentPath = currentPath[pathComponents[i]];
                }
                delete currentPath[pathComponents[pathComponents.length - 1]];
                break;
        }
    }
    return state;
}