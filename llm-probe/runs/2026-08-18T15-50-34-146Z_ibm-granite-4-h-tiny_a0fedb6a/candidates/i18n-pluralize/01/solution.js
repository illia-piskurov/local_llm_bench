export function solve(input) {
    const locales = input.locales[input.lang];
    if (!locales) return input.key;
    const key = locales[input.key];
    if (key === undefined) return input.key;

    const params = input.params;
    let result;
    if (typeof key === 'string') {
        result = key.replace(/{(\w+)}/g, (_, varName) => params[varName]);
    } else if (Array.isArray(key)) {
        // Plural case
        const count = Number(params.count);
        if (count === 0 && key.zero !== undefined) {
            result = key.zero;
        } else if (count === 1 && key.one !== undefined) {
            result = key.one.replace(/#/g, String(count));
        } else {
            result = key.other.replace(/#/g, String(count));
        }
    } else {
        result = key;
    }

    return result;
}