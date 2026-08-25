export function solve(input) {
    const state = JSON.parse(JSON.stringify(input.state));
    const actions = input.actions;

    /**
     * Helper function to safely set a value at a potentially deeply nested path,
     * creating objects if they do not exist (immutable update).
     * Returns the modified object reference.
     */
    function setDeep(obj, path, value) {
        const parts = path.split('.');
        let current = obj;

        for (let i = 0; i < parts.length - 1; i++) {
            const part = parts[i];
            if (!current[part] || typeof current[part] !== 'object' || Array.isArray(current[part]) === false) {
                current[part] = {};
            }
            current = current[part];
        }

        // Set the final value, ensuring immutability by returning a new object reference up the chain if possible.
        // Since we are modifying 'state' (which is a deep copy), standard assignment works within this scope,
        // but the caller must handle tracking changes across the action sequence.
        current[parts[parts.length - 1]] = value;
        return obj; // Returning original reference since we modified it in place within the context of 'state'
    }

    for (const action of actions) {
        const { type } = action;
        let newState = state;

        switch (type) {
            case 'SET': {
                const [path, value] = [action.path, action.value];
                const parts = path.split('.');
                let target = newState;

                for (let i = 0; i < parts.length - 1; i++) {
                    const part = parts[i];
                    if (!target[part] || typeof target[part] !== 'object' || Array.isArray(target[part]) === false) {
                        target[part] = {};
                    }
                    target = target[part];
                }
                target[parts[parts.length - 1]] = value;
                break;
            }

            case 'TOGGLE': {
                const [path] = [action.path.split('.')];
                let currentVal = state;
                let parent = null;
                let key = path[path.length - 1];
                let pathParts = path.slice(0, -1);

                // Find the parent object reference and the value
                for (const part of pathParts) {
                    if (!currentVal[part] || typeof currentVal[part] !== 'object' || Array.isArray(currentVal[part]) === false) {
                        // This should ideally not happen if state is well-formed, but handles setting up structure
                        currentVal[part] = {};
                    }
                    currentVal = currentVal[part];
                }

                if (typeof currentVal[key] === 'boolean') {
                    currentVal[key] = !currentVal[key];
                } else {
                    // If value is not boolean, set to true
                    currentVal[key] = true;
                }
                break;
            }

            case 'ARRAY_PUSH': {
                const [path, item] = [action.path.split('.'), action.item];
                let target = state;
                let parts = path.split('.');
                let arrIndex = -1;

                // Traverse to the array location
                for (let i = 0; i < parts.length - 1; i++) {
                    const part = parts[i];
                    if (!target[part] || Array.isArray(target[part]) === false) {
                        target[part] = []; // Initialize if missing or not an array
                    }
                    target = target[part];
                }

                // If the final target is an array, push the item
                if (Array.isArray(target)) {
                    target.push(item);
                }
                break;
            }

            case 'ARRAY_REMOVE': {
                const [path, indexStr] = [action.path.split('.'), action.index];
                let target = state;
                let parts = path.split('.');
                let targetArray = null;

                // Traverse to the array location
                for (let i = 0; i < parts.length - 1; i++) {
                    const part = parts[i];
                    if (!target[part] || Array.isArray(target[part]) === false) {
                        return; // Path invalid, cannot remove
                    }
                    target = target[part];
                }

                targetArray = target[parts[parts.length - 1]];

                if (Array.isArray(targetArray) && indexStr !== undefined && indexStr >= 0 && indexStr < targetArray.length) {
                    targetArray.splice(indexStr, 1);
                }
                break;
            }

            case 'DELETE': {
                const [path] = [action.path.split('.')];
                let current = state;
                let parent = null;
                let keyToDelete = path[path.length - 1];
                let pathParts = path.slice(0, -1);

                // Find the parent object reference
                for (const part of pathParts) {
                    if (!current[part] || typeof current[part] !== 'object') {
                        return; // Parent path invalid
                    }
                    parent = current;
                    current = current[part];
                }

                // Delete the key from the parent
                if (parent && Object.prototype.hasOwnProperty.call(parent, keyToDelete)) {
                    delete parent[keyToDelete];
                }
                break;
            }
        }
        state = newState; // Ensure state is updated for the next action
    }

    return state;
}