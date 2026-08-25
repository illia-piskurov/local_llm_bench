export function solve(input) {
  const locales = input.locales;
  const lang = input.lang;
  const key = input.key;
  const params = input.params;

  // Check if key exists in the specified locale
  const value = locales[lang]?.[key];

  // If not, check 'en' as fallback
  if (!value) {
    value = locales['en']?.[key];
  }

  // If key is still missing, return it as-is
  if (!value) {
    return key;
  }

  // Replace {var} with params[var] inside the value
  const replacedValue = value.replace('{var}', params[key]);

  // Check if the value is a plural object
  if (typeof replacedValue === 'object' && replacedValue !== null) {
    // Determine which version to use based on params.count and available keys
    let version;
    if (params.count === 0 && 'zero' in replacedValue) {
      version = 'zero';
    } else if (params.count === 1 && 'one' in replacedValue) {
      version = 'one';
    } else {
      version = 'other';
    }

    // Replace '#' with params.count inside the version string
    const versionStr = new Map(replacedValue).values()[version];
    const versionStrWithCount = versionStr.replace('#', params.count);

    // Return the final formatted string
    return `${params[count]} items, ${params[name]}`;
  } else {
    // If it's a simple string, just return it after replacing {var}
    return replacedValue;
  }
}