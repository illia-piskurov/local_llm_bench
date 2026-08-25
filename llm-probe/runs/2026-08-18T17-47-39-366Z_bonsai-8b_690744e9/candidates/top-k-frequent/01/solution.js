export function solve(input) {
  const counts = {};
  const numbers = input.numbers;

  for (const num of numbers) {
    counts[num] = (counts[num] || 0) + 1;
  }

  const sorted = Object.entries(counts)
    .sort((a, b) => {
      if (a[1] !== b[1]) return b[1] - a[1];
      return a[0] - b[0];
    });

  const result = [];
  for (let i = 0; i < sorted.length && i < input.k; i++) {
    result.push(sorted[i][0]);
  }

  return result;
}