export function solve(input) {
  const text = input.text;
  let maxLength = 0;
  let left = 0;
  const charMap = new Map();

  for (let right = 0; right < text.length; right++) {
    const char = text[right];
    if (charMap.has(char) && charMap.get(char) >= left) {
      left = charMap.get(char) + 1;
    }
    charMap.set(char, right);
    const currentLength = right - left + 1;
    if (currentLength > maxLength) {
      maxLength = currentLength;
    }
  }

  return maxLength;
}