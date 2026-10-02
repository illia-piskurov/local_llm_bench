export function solve(input) {
  const s = input.text;
  let left = 0;
  let maxLen = 0;
  const seen = new Map();
  for (let right = 0; right < s.length; right++) {
    const ch = s[right];
    if (seen.has(ch) && seen.get(ch) >= left) {
      left = seen.get(ch) + 1;
    }
    seen.set(ch, right);
    const curLen = right - left + 1;
    if (curLen > maxLen) maxLen = curLen;
  }
  return maxLen;
}