export function solve(input) {
  const { locales, lang, key, params } = input;

  // 1. Determine the base localized string (Lookup and Fallback)
  let localizedString = '';

  if (locales && locales[lang] && locales[lang][key] !== undefined) {
    localizedString = locales[lang][key];
  } else if (locales && locales['en'] && locales['en'][key] !== undefined) {
    localizedString = locales['en'][key];
  } else {
    // Fallback to key itself if not found anywhere
    return key;
  }

  // 2. Handle Pluralization (if localizedString is an object)
  let finalString = localizedString;

  if (typeof localizedString === 'object' && localizedString !== null) {
    const count = params ? params.count : undefined;

    let selectedString = '';

    if (count !== undefined) {
      if (localizedString.zero !== undefined && count === 0) {
        selectedString = localizedString.zero;
      } else if (localizedString.one !== undefined && count === 1) {
        selectedString = localizedString.one;
      } else {
        // Default to 'other' or the only available option
        selectedString = localizedString.other;
      }
    } else {
      // If count is missing, assume 'other' if it exists, otherwise use what we have (or default)
      selectedString = localizedString.other !== undefined ? localizedString.other : localizedString;
    }

    finalString = selectedString;
  }

  // 3. Perform Variable Substitution
  if (!finalString) {
    return '';
  }

  // Substitute general variables like {var}
  for (const varName in params) {
    if (params.hasOwnProperty(varName)) {
      const regex = new RegExp(`\\{${varName}\\}`, 'g');
      const replacement = String(params[varName]);
      finalString = finalString.replace(regex, replacement);
    }
  }

  // Substitute count marker '#' if we used a plural string
  if (typeof finalString === 'string' && (localizedString.zero || localizedString.one || localizedString.other)) {
    const countValue = params ? params.count : undefined;
    
    if (countValue !== undefined) {
      // Replace '#' with the count value (assuming it replaces the count in plural strings)
      finalString = finalString.replace(/#/g, String(countValue));
    }
  }

  return finalString;
}