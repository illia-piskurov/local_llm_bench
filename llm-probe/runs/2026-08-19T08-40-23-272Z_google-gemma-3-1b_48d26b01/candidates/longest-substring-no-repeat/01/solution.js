export function solve(input) {
  let maxLength = 0;
  let start = 0;
  const charSet = new Set();

  for (let end = 0; end < input.length; end++) {
    while (charSet.has(input[end])) {
      charSet.delete(input[start]);
      start++;
    }
    charSet.add(input[end]);
    maxLength = Math.max(maxLength, end - start + 1);
  }

  return maxLength;
}