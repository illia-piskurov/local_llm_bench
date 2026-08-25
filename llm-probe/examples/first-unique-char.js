export function solve(input) {
  const counts = new Map();
  for (const character of input.text) {
    counts.set(character, (counts.get(character) ?? 0) + 1);
  }
  for (let index = 0; index < input.text.length; index += 1) {
    if (counts.get(input.text[index]) === 1) return index;
  }
  return -1;
}
