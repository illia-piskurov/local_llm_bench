export function solve(input) {
    const { state, actions } = input;
    const resultState = JSON.parse(JSON.stringify(state));

    for (const action of actions) {
        if (action.type === 'SET') {
            const pathParts = action.path.split('.');
            let current = resultState;

            for (let i = 0; i < pathParts.length - 1; i++) {
                const part = pathParts[i];
                if (!current[part]) {
                    current[part] = {};
                }
                current = current[part];
            }

            current[pathParts[pathParts.length - 1]] = action.value;
        } else if (action.type === 'TOGGLE') {
            const pathParts = action.path.split('.');
            let current = resultState;

            for (const part of pathParts) {
                if (!current[part]) {
                    current[part] = false; // Default to false if missing
                }
                current = current[part];
            }

            if (typeof current === 'boolean') {
                current = !current;
            } else {
                current = true;
            }
        } else if (action.type === 'ARRAY_PUSH') {
            const pathParts = action.path.split('.');
            let current = resultState;

            for (const part of pathParts) {
                if (!current[part]) {
                    current[part] = [];
                }
                current = current[part];
            }

            current.push(action.item);
        } else if (action.type === 'ARRAY_REMOVE') {
            const pathParts = action.path.split('.');
            let current = resultState;

            for (const part of pathParts) {
                if (!current[part]) {
                    throw new Error(`Invalid path: ${action.path}`);
                }
                current = current[part];
            }

            if (Array.isArray(current)) {
                const index = action.index;
                if (index >= 0 && index < current.length) {
                    current.splice(index, 1);
                }
            } else {
                throw new Error(`Path ${action.path} is not an array`);
            }
        } else if (action.type === 'DELETE') {
            const pathParts = action.path.split('.');
            let current = resultState;

            for (let i = 0; i < pathParts.length - 1; i++) {
                const part = pathParts[i];
                if (!current[part]) {
                    throw new Error(`Invalid path: ${action.path}`);
                }
                current = current[part];
            }

            delete current[pathParts[pathParts.length - 1]];
        }
    }

    return resultState;
}