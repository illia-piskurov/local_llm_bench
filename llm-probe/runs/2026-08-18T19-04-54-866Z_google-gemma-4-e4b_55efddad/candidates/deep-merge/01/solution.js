export function solve(input) {
    if (!input || !input.objects || input.objects.length === 0) {
        return {};
    }

    /**
     * Checks if a value is a plain object (not null, not an array).
     * @param {*} obj The item to check.
     * @returns {boolean} True if it's a plain object.
     */
    function isPlainObject(obj) {
        return typeof obj === 'object' && obj !== null && !Array.isArray(obj);
    }

    /**
     * Recursively merges two objects: target (existing state) and source (new data).
     * Source overrides target, unless both values are plain objects, in which case they merge recursively.
     * Keys with undefined source values are ignored.
     * @param {object} target The accumulated object (non-mutated).
     * @param {object} source The new object to merge from.
     * @returns {object} A newly created merged object.
     */
    function deepMerge(target, source) {
        const result = { ...target };

        for (const key in source) {
            if (!source.hasOwnProperty(key)) continue;
            const sourceValue = source[key];
            const targetValue = target[key];

            // Rule: Keys with undefined value are ignored (previous value is retained).
            if (sourceValue === undefined) {
                continue;
            }

            let mergedValue;

            // Check for recursive merge condition: both values must be plain objects.
            if (isPlainObject(targetValue) && isPlainObject(sourceValue)) {
                mergedValue = deepMerge(targetValue, sourceValue);
            } else {
                // Rule: Arrays and primitive values are replaced entirely by the later value.
                // This handles cases where one or both inputs are non-plain objects (e.g., arrays, primitives).
                mergedValue = sourceValue;
            }

            result[key] = mergedValue;
        }
        return result;
    }


    // Use reduce to process the array of objects sequentially, merging each one into the accumulated result.
    const initialResult = {};
    return input.objects.reduce((accumulator, currentObject) => {
        // Ensure we treat everything as non-mutating copies for the merge operation.
        // The deepMerge function handles the necessary cloning and recursion.
        return deepMerge(accumulator, currentObject);
    }, initialResult);
}