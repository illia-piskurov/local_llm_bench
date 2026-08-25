export function solve(input) {
  const nums = input.numbers;
  const k = input.k;

  // Count frequencies
  const freqMap = new Map();
  for (const n of nums) {
    freqMap.set(n, (freqMap.get(n) || 0) + 1);
  }

  // Convert to array and sort by descending frequency, then ascending number
  const sorted = Array.from(freqMap.entries()).sort((a, b) => {
    if (b[1] !== a[1]) return b[1] - a[1]; // higher freq first
    return a[0] - b[0]; // lower number first
  });

  // Take top k numbers
  const result = sorted.slice(0, k).map(entry => entry[0]);

  return result;
}