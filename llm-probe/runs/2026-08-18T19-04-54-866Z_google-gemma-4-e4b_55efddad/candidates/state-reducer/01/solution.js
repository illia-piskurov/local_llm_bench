export function solve(input) {

    // Helper function to deep clone an object
    const deepClone = (obj) => JSON.parse(JSON.stringify(obj));

    /**
     * Helper function to set a value at a dot-separated path deeply within an object.
     * Returns a new, modified object copy.
     */
    const setDeepValue = (obj, path, value) => {
        if (!path || !typeof path) return deepClone(obj);

        const keys = path.split('.');
        let current = obj;
        let result = {};

        // Traverse and build the copy up to the parent of the target key
        for (let i = 0; i < keys.length - 1; i++) {
            const key = keys[i];
            // Must clone the intermediate structure if it exists, otherwise start a new object.
            if (current[key] === undefined) {
                result[key] = {};
                current = result[key];
            } else {
                let next = deepClone(current[key]);
                result[key] = next;
                current = next;
            }
        }

        // Handle the final key assignment
        const finalKey = keys[keys.length - 1];
        if (finalKey) {
             // If the path was just a single key, we assign directly to result
            if (keys.length === 1) {
                return deepClone(obj); // Re-cloning is necessary if no traversal occurred
            }

            // Assigning the final value
            let parent = current;
             // We must update the reference chain leading up to this point in 'result'
            if (keys.length > 1) {
                parent[finalKey] = value;
            } else {
                 // Handle single key assignment if necessary, though usually handled by path structure
                 return JSON.parse(JSON.stringify(obj));
            }

            return result;

        }
        return deepClone(obj); // Should not happen if path is valid
    };


    /**
     * Helper function to traverse and retrieve the parent object and key of a given path,
     * allowing modification/deletion without needing to pass through recursive cloning logic.
     * Returns { parent: Object, key: string | null } or null if impossible.
     */
    const getParentAndKey = (obj, path) => {
        if (!path || !typeof path) return { parent: null, key: null };

        const keys = path.split('.');
        if (keys.length === 1) {
            return { parent: obj, key: keys[0] };
        }

        let current = obj;
        for (let i = 0; i < keys.length - 1; i++) {
            const key = keys[i];
            if (!(current && typeof current === 'object' && current !== null) || !(key in current)) {
                return { parent: null, key: null }; // Path broken
            }
            current = current[key];
        }

        return { parent: current, key: keys[keys.length - 1] };
    };


    let currentState = deepClone(input.state);

    for (const action of input.actions) {
        let nextState = deepClone(currentState); // Start with a full clone for modification

        try {
            switch (action.type) {
                case 'SET': {
                    // SET: sets property at dot-separated path (creates nested objects if missing).
                    const value = action.value;
                    nextState = setDeepValue(currentState, action.path, value);
                    break;
                }

                case 'TOGGLE': {
                    // TOGGLE: negates boolean at path (if value is not boolean, sets true).
                    const pathComponents = action.path.split('.');
                    let currentObj = nextState;
                    let parentObj = null; // The object containing the final key

                    // Traverse to find the parent container and its key
                    for (let i = 0; i < pathComponents.length - 1; i++) {
                        const key = pathComponents[i];
                        if (!(currentObj && typeof currentObj === 'object' && currentObj !== null && key in currentObj)) {
                            // Path doesn't exist, treat it as SET to true
                            nextState = setDeepValue(currentState, action.path, true);
                            break; // Exit TOGGLE logic early if path is broken
                        }
                        parentObj = currentObj[key];
                        currentObj = parentObj;
                    }

                    if (i < pathComponents.length - 1) { // If we successfully reached the parent object
                        const finalKey = action.path.split('.').pop();
                        let currentValue;

                         // Attempt to retrieve current value without modifying nextState yet
                        let tempCheck = currentState;
                        for(const key of pathComponents) {
                            if (key in tempCheck && typeof tempCheck[key] !== 'undefined') {
                                tempCheck = tempCheck[key];
                            } else {
                                currentValue = undefined; // Path broken in original state
                                break;
                            }
                        }

                        // Recalculate the value based on the rule: !bool or true if not bool/missing.
                        const newValue = typeof currentState === 'object' && currentValue !== undefined 
                                        ? (typeof currentValue === 'boolean' ? !currentValue : true) 
                                        : true;

                        nextState = setDeepValue(currentState, action.path, newValue);
                    } else {
                        // Handle case where path is too short or broken early
                         nextState = setDeepValue(currentState, action.path, true);
                    }
                    break;
                }

                case 'ARRAY_PUSH': {
                    // ARRAY_PUSH: appends item to array at path (creates [item] if array missing).
                    const item = action.item;
                    let currentArray = null;
                    let parentContainer = nextState; // Start from root of the copy

                    // 1. Find Parent Container and check/ensure it's an array
                    for (const key of action.path.split('.')) {
                        if (!(key in parentContainer) && !['', ''].includes(key)) {
                             // If intermediate path doesn't exist, we can't push reliably unless it's the first item
                             parentContainer = nextState; // Fall back to root? Complex state logic needed.
                             break; 
                        }
                         parentContainer = parentContainer[key];
                    }

                    if (Array.isArray(currentState) || typeof currentState === 'object' && currentState !== null && Array.isArray(currentState)) {
                        // If the current object *is* an array, use it directly as container for simplicity in this implementation structure
                        currentArray = parentContainer; 
                    } else if (typeof nextState[action.path] === 'undefined') {
                        // If target doesn't exist, set it to [item]
                        nextState = setDeepValue(currentState, action.path, [item]);
                        break;
                    }


                    const pathKeys = action.path.split('.');

                    let resultContainer = deepClone(nextState); // Must operate on a copy of the container structure

                    // Traverse to the parent object of the array target
                    if (pathKeys.length === 1) {
                        // Pushing directly to root state (unlikely but safe check)
                        resultContainer = deepClone(currentState);
                        resultContainer[action.path] = Array.isArray(currentState[action.path]) ? [...currentState[action.path], item] : [item];

                    } else {
                        // Navigate to parent and rebuild the path up to this point
                        let currentCopy = resultContainer;
                        for (let i = 0; i < pathKeys.length - 1; i++) {
                            const key = pathKeys[i];
                            if (!(key in currentCopy)) break; // Safety break

                            // Clone the structure up to the parent
                             let nextLevel = deepClone(currentCopy[key]);
                             
                             // Check if we need to modify this level (the array)
                             const targetKey = pathKeys[i+1];
                             if (targetKey === pathKeys[pathKeys.length - 1]) {
                                 // This is the parent of the array, and we are adding the item here. Skip complex cloning for now.
                             }

                            // Rebuild structure up to parent
                            let temp = {};
                            for(const k in currentCopy) {
                                if (k === key) temp[k] = nextLevel;
                                else temp[k] = currentCopy[k];
                            }
                            currentCopy = temp;
                        }

                        // Re-implementing PUSH robustly via path components:
                        let newStructure = deepClone(currentState);
                        const keysToParent = action.path.split('.');
                         if (keysToParent.length > 0) {
                            let parentTarget = newStructure;
                             for (let i = 0; i < keysToParent.length - 1; i++) {
                                 const key = keysToParent[i];
                                 // Clone the structure up to this point
                                 if (!parentTarget[key] || !Array.isArray(parentTarget[key])) {
                                     parentTarget[key] = []; // Ensure it's an array before pushing
                                 } else if (typeof parentTarget[key] !== 'object') {
                                     // If path dictates a non-array type, we fail gracefully or overwrite. Assuming successful structure setup for now.
                                     parentTarget[key] = []; 
                                 }

                                 let nextLevelCopy = deepClone(parentTarget[key]);
                                 // Ensure the new level is an array before assignment
                                 if (!Array.isArray(nextLevelCopy)) {
                                     nextLevelCopy = [];
                                 }
                                 parentTarget[key] = nextLevelCopy;
                                 parentTarget = nextLevelCopy;
                             }

                            const finalParentKey = keysToParent[keysToParent.length - 1];
                            if(typeof parentTarget === 'object' && parentTarget !== null) {
                                if (Array.isArray(parentTarget)) {
                                     // Success: Append item to the array structure already built in newStructure
                                     parentTarget.push(item); // Note: This mutates parentTarget, but since parentTarget is a copy of an intermediate state object inside newStructure, this works functionally for the loop iteration.
                                 } else {
                                     // Fallback if path setup failed to result in an array at the target location
                                     setDeepValue(currentState, action.path, [item]); 
                                 }
                            } else {
                                // If parentTarget wasn't successfully navigated/created
                                setDeepValue(currentState, action.path, [...(Array.isArray(currentState) ? currentState : []), item]);
                            }

                        }
                        nextState = newStructure;
                    }


                    break;
                }

                case 'ARRAY_REMOVE': {
                    // ARRAY_REMOVE: removes element at index if within bounds.
                    const keysToRemove = action.path.split('.');

                    if (keysToRemove.length === 0) break;

                    let currentContainer = currentState;
                    let parentContainer = null;
                    let targetKey = null;

                     // Traverse to find the immediate parent and key of the array
                    for(let i=0; i < keysToRemove.length - 1; i++) {
                        const key = keysToRemove[i];
                        if (!(key in currentContainer)) break; // Path broken
                        parentContainer = currentContainer[key];
                        currentContainer = parentContainer;
                    }
                    targetKey = keysToRemove[keysToRemove.length - 1];

                    // Check if the target location is an array and bounds are valid
                    if (typeof currentContainer === 'object' && currentContainer !== null && Array.isArray(currentContainer) && action.index >= 0 && action.index < currentContainer.length) {
                        // Remove item by slicing, ensuring immutability
                        const newArray = [...currentContainer];
                        newArray.splice(action.index, 1);

                        // Rebuild state using the slice operation on the path
                        let tempState = deepClone(currentState);
                        let currentCopy = tempState;

                        for (let i = 0; i < keysToRemove.length - 2; i++) { // Up to parent of array
                            const key = keysToRemove[i];
                             // Clone structure up to this point
                            let nextLevelCopy = deepClone(currentCopy[key]);
                            if (!Array.isArray(nextLevelCopy)) nextLevelCopy = [];

                            // Rebuild path
                            let tempParent = {};
                            for(const k in currentCopy) {
                                if (k === key) tempParent[k] = nextLevelCopy;
                                else tempParent[k] = currentCopy[k];
                            }
                            currentCopy = tempParent;

                        }
                        // Set the new array slice at the end of the path
                        nextState = setDeepValue(currentState, action.path, newArray);
                    } else {
                         // If removal fails (not an array or out of bounds), state remains unchanged in this step.
                    }
                    break;
                }

                case 'DELETE': {
                    // DELETE: deletes key at path.
                     const keysToDelete = action.path.split('.');

                    if (keysToDelete.length === 0) break;

                    let currentObj = currentState;
                    let parentObj = null;
                    let finalKey = null;

                    for (let i = 0; i < keysToDelete.length - 1; i++) {
                        const key = keysToDelete[i];
                        if (!(key in currentObj)) break;
                        parentObj = currentObj[key];
                        currentObj = parentObj;
                    }

                    finalKey = keysToDelete[keysToDelete.length - 1];

                     // If we found a valid parent and key, we need to rebuild the state without that key.
                    if (typeof parentObj === 'object' && parentObj !== null && finalKey in parentObj) {
                        let tempState = deepClone(currentState);

                        // Traverse path components up to the parent object
                         let currentCopy = tempState;
                         for (let i = 0; i < keysToDelete.length - 2; i++) {
                             const key = keysToDelete[i];

                              let nextLevelCopy = deepClone(currentCopy[key]);
                             if (!Array.isArray(nextLevelCopy)) nextLevelCopy = [];


                            // Rebuild path structure up to the parent container's siblings
                            let tempParent = {};
                            for(const k in currentCopy) {
                                if (k === key) tempParent[k] = nextLevelCopy;
                                else tempParent[k] = currentCopy[k];
                            }
                            currentCopy = tempParent;
                         }

                        // Final deletion: clone parentObj and remove the key
                        let newParent = {};
                        for (const k in parentObj) {
                             if(k !== finalKey) {
                                 newParent[k] = parentObj[k];
                             }
                        }

                        // Re-assign the modified parent back into the structure. This is complex due to deep cloning state.
                        // We rely on setDeepValue being able to handle nested replacement correctly based on paths.
                        // However, since deletion changes object topology, simple SET might not work if the path is complex.

                         let finalStructure = deepClone(currentState); // Start with clean clone
                         const keysToParent = keysToDelete;

                          if (keysToParent.length > 0) {
                             // Re-implementing DELETE using recursive cloning logic for robustness:
                              function deleteRecursive(obj, path) {
                                   const keys = path.split('.');
                                   let newObj = {};
                                   for (const key in obj) {
                                       if (key === keys[0]) {
                                           // This is the target level we are recursing into. Recurse or handle deletion here.
                                            if(keys.length > 1) {
                                                newObj[key] = deleteRecursive(obj[key], path.substring(key.length + 1).trim());
                                            } else {
                                                // This key is the target for deletion
                                                continue; // Skip adding this key to the new object
                                            }
                                       } else {
                                           newObj[key] = obj[key];
                                       }
                                   }
                                   return newObj;
                              }

                             // Simplified approach: if we delete a leaf node, we just set it as undefined/null which is usually sufficient for JSON compatibility unless the whole object needs structural rebuild.
                             setDeepValue(currentState, action.path, undefined); // This sets the key to undefined (which might be dropped later)
                             nextState = deepClone(currentState);

                          } else {
                              // Cannot delete from empty path
                              nextState = currentState;
                          }


                    break;
                }

            }
        } catch (e) {
             // If any action fails due to structural issues or missing paths, log and keep the state stable.
             console.error(`Error applying action ${JSON.stringify(action)}:`, e);
        }

        currentState = nextState;
    }


    return currentState;
}