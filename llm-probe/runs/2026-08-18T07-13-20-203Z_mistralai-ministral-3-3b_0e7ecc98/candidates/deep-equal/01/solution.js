export function solve(input) {
    const isEqual = (a, b) => {
        if (a === b) return true;

        // Handle primitives and null
        if (typeof a !== 'object' || typeof b !== 'object' || a === null || b === null) {
            return false;
        }

        // Handle arrays
        if (Array.isArray(a) && Array.isArray(b)) {
            if (a.length !== b.length) return false;
            for (let i = 0; i < a.length; i++) {
                if (!isEqual(a[i], b[i])) return false;
            }
            return true;
        }

        // Handle plain objects
        const keysA = new Set(Object.keys(a));
        const keysB = new Set(Object.keys(b));

        if (keysA.size !== keysB.size) return false;

        for (const key of keysA) {
            if (!keysB.has(key) || !isEqual(a[key], b[key])) {
                return false;
            }
        }

        return true;
    };

    return isEqual(input.a, input.b);
}