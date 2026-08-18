export function solve(input) {
    /**
     * Helper function to check if two values are deeply equal.
     * Handles primitives, null, arrays, and plain objects.
     */
    const isDeepEqual = (a, b) => {
        // 1. Strict equality handles identical references, numbers, strings, booleans, undefined, and null === null
        if (a === b) return true;

        // 2. Handle non-primitive comparisons involving null or type mismatches
        // If one is null/undefined or if types differ significantly after initial checks, they are not equal.
        const typeA = typeof a;
        const typeB = typeof b;

        if (a === null || typeA !== 'object' || b === null || typeB !== 'object') {
            // If we reached here, and they weren't strictly equal, and at least one is not an object,
            // or if either is null, they must be unequal. (E.g., 1 != "1", [] != {})
            return false;
        }

        const isArrayA = Array.isArray(a);
        const isArrayB = Array.isArray(b);

        // 3. Type checking for structural mismatch (Array vs Object)
        if (isArrayA !== isArrayB) {
            return false;
        }

        // --- Handle Arrays ---
        if (isArrayA) { // Both are arrays
            const len = a.length;
            if (len !== b.length) return false;

            for (let i = 0; i < len; i++) {
                if (!isDeepEqual(a[i], b[i])) {
                    return false;
                }
            }
            return true;
        }


        // --- Handle Objects ---
        const keysA = Object.keys(a);
        const keysB = Object.keys(b);

        // Check key count
        if (keysA.length !== keysB.length) {
            return false;
        }

        for (let i = 0; i < keysA.length; i++) {
            const key = keysA[i];

            // Check if the corresponding key exists in B
            if (!Object.prototype.hasOwnProperty.call(b, key)) {
                return false;
            }

            // Recurse comparison for values
            if (!isDeepEqual(a[key], b[key])) {
                return false;
            }
        }

        return true;
    };

    // The goal is to compare input.a and input.b
    return isDeepEqual(input.a, input.b);
}