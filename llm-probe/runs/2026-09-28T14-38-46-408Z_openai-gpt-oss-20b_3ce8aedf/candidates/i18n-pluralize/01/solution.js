<|channel|>final code<|message|>export function solve(input) {
  // Deep copy params to avoid mutation
  const { locales, lang, key, params } = input;
  // Helper to get translation string or object
  const getTrans = (l) => {
    if (!locales[l]) return undefined;
    return locales[l][key];
  };
  let trans = getTrans(lang);
  if (trans === undefined) {
    trans = getTrans('en');
  }
  if (trans === undefined) {
    return key;
  }

  // Determine the string to use
  let str = '';
  if (typeof trans === 'string') {
    str = trans;
  } else if (typeof trans === 'object' && trans !== null) {
    const count = params.count;
    if (count === 0 && typeof trans.zero === 'string') {
      str = trans.zero;
    } else if (count === 1 && typeof trans.one === 'string') {
      str = trans.one;
    } else if (typeof trans.other === 'string') {
      str = trans.other;
    } else {
      // Fallback if unexpected plural structure
      return key;
    }
  } else {
    return key;
  }

  // Replace placeholders
  const replacePlaceholders = (s) => {
    return s.replace(/{([^}]+)}/g, (_, varName) => {
      if (varName === '#') return params.count !== undefined ? String(params.count) : '#';
      return params[varName] !== undefined ? String(params[varName]) : `{${varName}}`;
    });
  };

  // Handle '#' replacement inside plural strings
  if (str.includes('#')) {
    str = replacePlaceholders(str);
  }
  // Replace other placeholders
  str = str.replace(/{([^}]+)}/g, (_, varName) => {
    return params[varName] !== undefined ? String(params[varName]) : `{${varName}}`;
  });

  return str;
}