export function solve(input) {
  if (!input || !input.numbers || input.numbers.length === 0) {
    return [];
  }

  const frequencies = {};
  for (const num of input.numbers) {
    frequencies[num] = (frequencies[num] || 0) + 1;
  }

  const sortedFrequencies = Object.entries(frequencies).sort((a, b) => b[1] - a[1]);

  return sortedFrequencies.map(item => item[0]);
}