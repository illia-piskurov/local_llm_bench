export function solve(input) {
    if (!input?.objects || input.objects.length === 0) return {};

    const result = {};
    let current = result;

    for (const obj of input.objects) {
        for (const key in obj) {
            const value = obj[key];
            if (value === undefined) continue;

            if (typeof value === 'object' && !Array.isArray(value)) {
                if (!(key in current)) {
                    current[key] = {};
                    current = current[key];
                } else if (!Array.isArray(current[key]) && typeof current[key] === 'object') {
                    const merged = mergeObjects([current[key], value]);
                    Object.assign(current[key], merged);
                    current = current[key];
                }
            } else {
                current[key] = value;
            }
        }

        // Reset for next object
        current = result;
    }

    return result;
}

function mergeObjects(objects) {
    const result = {};
    let current = result;

    for (const obj of objects) {
        if (!obj || typeof obj !== 'object') continue;

        for (const key in obj) {
            const value = obj[key];
            if (value === undefined) continue;

            if (typeof value === 'object' && !Array.isArray(value)) {
                if (!(key in current)) {
                    current[key] = {};
                    current = current[key];
                } else if (!Array.isArray(current[key]) && typeof current[key] === 'object') {
                    const merged = mergeObjects([current[key], value]);
                    Object.assign(current[key], merged);
                    current = current[key];
                }
            } else {
                current[key] = value;
            }
        }

        current = result;
    }

    return result;
}