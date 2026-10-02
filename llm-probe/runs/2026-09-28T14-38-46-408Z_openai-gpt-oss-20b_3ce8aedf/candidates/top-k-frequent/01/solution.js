export function solve(input) {
  const { numbers, k } = input;
  const freqMap = new Map();
  for (const n of numbers) {
    freqMap.set(n, (freqMap.get(n) || 0) + 1);
  }
  const sorted = Array.from(freqMap.entries())
    .sort((a, b) => {
      if (b[1] !== a[1]) return b[1] - a[1];
      return a[0] - b[0];
    })
    .slice(0, k)
    .map(([num]) => num);
  return sorted;
}