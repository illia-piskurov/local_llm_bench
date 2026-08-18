export function solve(input) {
  const text = input.text;
  let start = 0,
      seen = new Map(),
      maxLen = 0;

  for (let end = 0; end < text.length; end++) {
    while (seen.has(text[end]) && seen.get(text[end]) >= start) {
      seen.delete(text[start]);
      start++;
    }
    seen.set(text[end], end);
    maxLen = Math.max(maxLen, end - start + 1);
  }

  return { length: maxLen };
}