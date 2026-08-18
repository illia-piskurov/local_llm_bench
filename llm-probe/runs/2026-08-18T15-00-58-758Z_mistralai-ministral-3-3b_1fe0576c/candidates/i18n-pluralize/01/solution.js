export function solve(input) {
    const { locales, lang = 'en', key, params = {} } = input;
    const locale = locales[lang] || {};
    const translation = locale[key] || locale['default'] || key;

    if (typeof translation === 'object' && !Array.isArray(translation)) {
        const { zero, one, other } = translation;
        return replacePlural(
            zero ?? one ?? other,
            params.count
        );
    }

    return translation.replace(/\{([^}]+)\}/g, (_, varName) => String(params[varName] || ''));
}

function replacePlural(str, count) {
    const { zero, one, other } = str;
    if (zero && count === 0) return zero;
    if (one && count === 1) return one;
    return str.replace(/#/g, String(count));
}