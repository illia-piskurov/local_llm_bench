export function solve(input) {
    const mergeObjects = (a, b) => {
        const result = {};
        for (const [k, v2] of Object.entries(b)) {
            if (v2 === undefined) continue; // ignore key, keep previous value
            if (v2 && typeof v2 === 'object' && !Array.isArray(v2)) {
                const aVal = a[k];
                result[k] = mergeObjects(aVal ? aVal : {}, v2);
            } else {
                result[k] = v2;
            }
        }
        return result;
    };
    const objects = input?.objects ?? [];
    let merged = {};
    for (const obj of objects) merged = mergeObjects(merged, obj);
    return merged || {};
}