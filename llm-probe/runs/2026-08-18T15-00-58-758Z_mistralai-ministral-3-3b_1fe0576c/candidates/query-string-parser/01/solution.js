export function solve(input) {
    const query = input.query.startsWith('?') ? input.query.slice(1) : input.query;
    if (!query) return {};

    const pairs = query.split('&').map(pair => pair.trim());
    const result = {};

    for (const [key, value] of pairs.map(pair => {
        const [k, v] = pair.split('=');
        return [decodeURIComponent(k || 'true'), decodeURIComponent(v || '')];
    })) {
        let current = result;
        const parts = key.split(/\[|\]/);

        for (let i = 0; i < parts.length - 1; i++) {
            const part = parts[i];
            if (!current[part]) {
                current[part] = typeof parts[i + 1] === 'string' && parts[i + 1].endsWith('[]') ? [] : {};
            }
            current = current[part];
        }

        const lastPart = parts.pop();
        if (lastPart.endsWith('[]')) {
            const arrayKey = lastPart.slice(0, -2);
            if (!current[arrayKey]) current[arrayKey] = [];
            current[arrayKey].push(value === 'true' ? true : value === 'false' ? false : Number.isFinite(Number(value)) ? Number(value) : value);
        } else {
            const parsedValue =
                value.toLowerCase() === 'true' ? true :
                value.toLowerCase() === 'false' ? false :
                Number.isFinite(Number(value)) ? Number(value) : value;
            current[lastPart] = parsedValue;
        }
    }

    return result;
}