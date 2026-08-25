export function solve(input) {
    const { locales, lang, key, params } = input;
    let targetValue = null;

    // --- 1. Find Localization Target (Handling Fallbacks) ---

    // Attempt to get value from specified locale: locales[lang][key]
    if (locales && locales[lang] && locales[lang][key]) {
        targetValue = locales[lang][key];
    } else if (locales && locales['en'] && locales['en'][key]) {
        // Fallback to 'en' locale: locales[en][key]
        targetValue = locales['en'][key];
    }

    let finalString;

    // --- 2. Determine Final String based on Type (Handling Plurals) ---

    if (typeof targetValue === 'object' && targetValue !== null && !Array.isArray(targetValue)) {
        // Potential plural object structure
        const count = parseInt(params.count);
        let selectedStringKey = '';

        if (count === 0 && targetValue.zero) {
            selectedStringKey = 'zero';
        } else if (count === 1 && targetValue.one) {
            selectedStringKey = 'one';
        } else if (targetValue.other) {
            selectedStringKey = 'other';
        }

        if (selectedStringKey) {
            finalString = targetValue[selectedStringKey];
        } else {
            // If parameters fail to select a plural form, we assume the key itself is used if no string version was found.
            return key;
        }

    } else if (typeof targetValue === 'string') {
        finalString = targetValue;
    } else {
        // Fallback: If nothing found in locales, return the key itself
        return key;
    }

    // --- 3. Substitute Variables and Count Marker (#) ---

    let result = String(finalString);

    // A. Substitute general variables {var}
    // Matches patterns like {name}, {id}, etc.
    result = result.replace(/\{(\w+)\}/g, (match, varName) => {
        if (params && params.hasOwnProperty(varName)) {
            return String(params[varName]);
        }
        // If parameter is missing, leave the placeholder unchanged
        return match;
    });

    // B. Substitute count marker # with actual count value
    const count = parseInt(params.count) || 0;
    result = result.replace(/#/g, String(count));

    return result;
}