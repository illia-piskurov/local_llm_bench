export function solve(input) {
    function isObject(item) {
        return item && typeof item === 'object' && !Array.isArray(item);
    }

    function fromJSON(input) {
        if (typeof input !== 'object' || input === null) {
            return input === null ? { type: 'null', value: true } : { type: 'primitive', value: input };
        } else if (Array.isArray(input)) {
            return { type: 'array', elements: input.map(fromJSON) };
        } else if (isObject(input)) {
            const obj = {};
            for (const key in input) {
                if (Object.prototype.hasOwnProperty.call(input, key)) {
                    obj[key] = fromJSON(input[key]);
                }
            }
            return { type: 'object', data: obj };
        }
        return null; // Should not happen for valid JSON structures
    }

    function deepEquals(obj1, obj2) {
        if (typeof obj1 !== typeof obj2) return false;

        // Primitives and null check
        if (typeof obj1 !== 'object' || obj1 === null) {
            return obj1 === obj2;
        }

        const isArray1 = Array.isArray(obj1);
        const isArray2 = Array.isArray(obj2);

        // Type mismatch check (Array vs Object/Primitive)
        if (isArray1 !== isArray2) return false;

        // Case 1: Arrays
        if (isArray1 && isArray2) {
            if (obj1.length !== obj2.length) return false;
            for (let i = 0; i < obj1.length; i++) {
                if (!deepEquals(obj1[i], obj2[i])) {
                    return false;
                }
            }
            return true;
        }

        // Case 2: Plain Objects
        if (isObject(obj1) && isObject(obj2)) {
            const keys1 = Object.keys(obj1);
            const keys2 = Object.keys(obj2);

            if (keys1.length !== keys2.length) return false;

            for (let i = 0; i < keys1.length; i++) {
                const key = keys1[i];

                // Check if the second object has the same key
                if (!Object.prototype.hasOwnProperty.call(obj2, key)) return false;

                if (!deepEquals(obj1[key], obj2[key])) {
                    return false;
                }
            }
            return true;
        }

        // Fallback for other types (e.g., functions, Dates if not handled above)
        // Since we assume JSON-compatible input, this should handle objects correctly.
        return obj1 === obj2;
    }

    return deepEquals(input.a, input.b);
}