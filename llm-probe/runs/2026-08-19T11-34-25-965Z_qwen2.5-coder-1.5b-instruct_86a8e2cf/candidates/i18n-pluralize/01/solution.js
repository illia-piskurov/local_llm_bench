export function solve(input) {
    const lang = input.locales[input.lang] || {};
    const key = input.key;

    if (key in lang) {
        let text = lang[key];
        if (typeof text === 'object') {
            for (const [countKey, countValue] of Object.entries(text)) {
                const param = input.params[countKey] || '';
                if (param) {
                    text = text[countKey].replace('#', param);
                    break;
                }
            }
        } else {
            for (let i = 0; i < text.length; i++) {
                if (text[i] === '{') {
                    const varIndex = text.indexOf('}', i + 1);
                    const varName = text.substring(i + 1, varIndex).toLowerCase();
                    const varValue = input.params[varName] || '';
                    text = text.replace(`{${varName}}`, varValue);
                }
            }
        }
    } else {
        return key;
    }

    return text;
}