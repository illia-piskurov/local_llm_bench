export function solve(input) {
  const { numbers } = input;
  const freq = {};
  numbers.forEach(n => {
    freq[n] = (freq[n] || 0) + 1;
  });
  const sorted = Object.entries(freq)
    .sort((a, b) => {
      const freqDiff = b[1] - a[1];
      if (freqDiff === 0) return a[0] - b[0];
      return freqDiff;
    })
    .map(([num]) => num);
  return sorted.slice(0, k).map(Number);
}