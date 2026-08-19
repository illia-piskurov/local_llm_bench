export function solve(input) {
  const { numbers, k } = input;
  
  // Create a frequency map of the numbers
  const frequencyMap = {};
  for (const num of numbers) {
    frequencyMap[num] = (frequencyMap[num] || 0) + 1;
  }
  
  // Convert the frequency map into an array of [number, frequency] pairs
  const frequencyPairs = Object.entries(frequencyMap);
  
  // Sort the pairs by descending frequency, then by ascending number
  frequencyPairs.sort((a, b) => {
    if (b[1] === a[1]) {
      return Number.parseInt(a[0], 10) - Number.parseInt(b[0], 10); // Ascending order for ties
    }
    return b[1] - a[1]; // Descending order by frequency
  });
  
  // Extract the top k numbers from the sorted pairs
  const result = frequencyPairs.slice(0, k).map(pair => Number.parseInt(pair[0], 10));
  
  return result;
}