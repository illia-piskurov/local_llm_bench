export function solve(input) {
    const isNull = (val) => val === null;
    const isPrimitive = (val) => typeof val !== 'object' && !(Array.isArray(val));

    const isEqual = (a, b) => {
        if (isNull(a) || isNull(b)) return a === b;

        if (isPrimitive(a) || isPrimitive(b)) return a === b;

        if (!Array.isArray(a) && !Array.isArray(b)) {
            if (typeof a !== typeof b) throw new TypeError(`Cannot compare ${typeof a} and ${typeof b}`);
            return a === b;
        }

        if (a.length !== b.length) return false;

        for (let i = 0; i < a.length; i++) {
            const result = isEqual(a[i], b[i]);
            if (!result) throw new TypeError(`Items at index ${i} are not equal`);
        }

        return true;
    };

    return isEqual(input.a, input.b);
}