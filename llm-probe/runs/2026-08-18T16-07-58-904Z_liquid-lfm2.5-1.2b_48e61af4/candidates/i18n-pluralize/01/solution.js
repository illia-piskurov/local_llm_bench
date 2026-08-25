export function solve(input) {
  const locales = input.locales || {};
  const lang = input.lang;
  const key = input.key;
  const params = input.params || {};
  const locale = locales[lang] || locales['en'];
  const value = locale[key];

  if (typeof value === 'object' && value.count === 0) {
    return params.count === 0 ? 'zero' : params.count === 1 ? 'one' : value.other;
  }
  return value.replace('#', params.count);
}