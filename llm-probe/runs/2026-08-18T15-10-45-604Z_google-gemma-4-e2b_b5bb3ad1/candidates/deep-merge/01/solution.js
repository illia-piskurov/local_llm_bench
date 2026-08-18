export function solve(input) {
    if (!input || !Array.isArray(input.objects) || input.objects.length === 0) {
        return {};
    }

    /**
     * Deeply merges source properties into target, ensuring immutability.
     * Later values override earlier ones based on the merge order.
     * Arrays and primitives are replaced.
     */
    function deepMerge(target, source) {
        // Create a shallow copy of the target to ensure immutability of the input object being merged into
        const output = { ...target };

        for (const key in source) {
            if (!Object.prototype.hasOwnProperty.call(source, key)) continue;

            const tVal = output[key];
            const sVal = source[key];

            // Rule: Keys with undefined value are ignored (previous value is retained).
            // This check primarily applies when the incoming value itself is undefined.
            if (sVal === undefined) {
                continue; 
            }

            const tIsObject = tVal && typeof tVal === 'object' && !Array.isArray(tVal);
            const sIsObject = sVal && typeof sVal === 'object' && !Array.isArray(sVal);

            if (tIsObject && sIsObject) {
                // Recursive merge for plain objects
                output[key] = deepMerge(tVal, sVal);
            } else if (Array.isArray(sVal)) {
                // Arrays are replaced entirely by the source array (Rule: arrays replaced entirely)
                // We copy the array to ensure immutability of the output structure itself.
                output[key] = [...sVal];
            } else {
                // Primitives, functions, or mixed types replace the target value
                output[key] = sVal;
            }
        }
        return output;
    }

    let result = {};

    for (const obj of input.objects) {
        if (typeof obj === 'object' && obj !== null) {
            // If result is empty, initialize it with the current object structure.
            if (Object.keys(result).length === 0) {
                result = deepMerge({}, obj);
            } else {
                // Merge the next object into the running result
                result = deepMerge(result, obj);
            }
        }
    }

    return result;
}