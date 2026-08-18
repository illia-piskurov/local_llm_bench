export function solve(input) {
  const counts = {};
  for (const num of input.numbers) {
    counts[num] = (counts[num] || 0) + 1;
  }
  
  const sortedNumbers = Object.entries(counts).sort((a, b) => {
    if (b[1] !== a[1]) {
      return b[1] - a[1];
    } else {
      return a[0] - b[0];
    }
  });
  
  return sortedNumbers.slice(0, input.k).map(([num]) => Number(num));
}