export function solve(input) {
    const query = input.query.startsWith('?') ? input.query.slice(1) : input.query;
    if (!query) return {};

    const pairs = query.split('&').map(pair => pair.trim());
    const result = {};
    let currentKey = '';

    for (const pair of pairs) {
        const [key, value] = pair.split('=', 2);
        const decodedKey = decodeURIComponent(key || '');
        const decodedValue = key ? decodeURIComponent(value) : true;

        if (!currentKey) {
            currentKey = decodedKey;
        }

        if (decodedKey.endsWith('[]')) {
            const baseKey = decodedKey.slice(0, -2);
            if (!(baseKey in result)) {
                result[baseKey] = [];
            }
            if (!Array.isArray(result[baseKey])) {
                result[baseKey] = [result[baseKey]];
            }
            if (typeof decodedValue === 'string' && !isNaN(decodedValue) && isFinite(decodedValue)) {
                const num = Number(decodedValue);
                if (Number.isInteger(num)) {
                    result[baseKey].push(Number(num));
                } else {
                    result[baseKey].push(num);
                }
            } else if (decodedValue === 'true') {
                result[baseKey].push(true);
            } else if (decodedValue === 'false') {
                result[baseKey].push(false);
            } else {
                result[baseKey].push(decodedValue);
            }
        } else if (decodedKey.includes('[')) {
            const parts = decodedKey.split('[');
            let currentObj = result;
            for (let i = 0; i < parts.length - 1; i++) {
                const part = parts[i];
                const nextPart = parts[i + 1].replace(/]$/, '');
                if (!currentObj[part]) {
                    currentObj[part] = {};
                }
                currentObj = currentObj[part];
            }
            const lastKey = parts.slice(-1)[0];
            const nestedKey = lastKey.replace(/]$/, '');
            const valueToStore = decodedValue;
            if (typeof valueToStore === 'string' && !isNaN(valueToStore) && isFinite(valueToStore)) {
                currentObj[nestedKey] = Number(valueToStore);
            } else if (valueToStore === 'true') {
                currentObj[nestedKey] = true;
            } else if (valueToStore === 'false') {
                currentObj[nestedKey] = false;
            } else {
                currentObj[nestedKey] = valueToStore;
            }
        } else {
            const processedValue = decodedValue === 'true' ? true : decodedValue === 'false' ? false :
                typeof decodedValue === 'string' && !isNaN(decodedValue) && isFinite(decodedValue) ?
                Number(decodedValue) : decodedValue;
            result[currentKey] = processedValue;
        }
    }

    return result;
}