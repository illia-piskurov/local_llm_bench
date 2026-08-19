export function solve(input) {
  const anagramGroups = {};
  for (const word of input.words) {
    const sortedWord = word.split("").sort().join("");
    if (!anagramGroups[sortedWord]) {
      anagramGroups[sortedWord] = [];
    }
    anagramGroups[sortedWord].push(word);
  }

  const result = Object.entries(anagramGroups).sort(([, valueA], [, valueB]) => valueA - valueB).map(([key]) => key);

  return result;
}