export function solve(input) {
    const locales = input.locales;
    const lang = input.lang;
    const key = input.key;
    const params = input.params;

    // Helper function to handle plural strings
    function formatPlural(str, count, name) {
        if (typeof str === 'object') {
            const pluralForm = Object.keys(str).find(pluralKey => {
                switch (pluralKey) {
                    case 'zero':
                        return count === 0;
                    case 'one':
                        return count === 1;
                    default:
                        return true;
                }
            });
            if (pluralForm) {
                return str[pluralForm].replace(/#/, params.count);
            }
        }
        return str.replace(/\{name\}/, name).replace(/\{count\}/, params.count);
    }

    // Find the localized key
    let localeKey = locales[lang] && locales[lang][key];
    if (!localeKey) {
        localeKey = locales['en'] && locales['en'][key];
    }
    
    // If still not found, use the key itself
    if (!localeKey) {
        return key;
    }

    // Format and return the string
    return formatPlural(localeKey, params.count, params.name);
}