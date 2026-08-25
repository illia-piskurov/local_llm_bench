export function solve(input) {
    const wordMap = new Map();

    for (const word of input.words) {
        const sortedWord = word.split('').sort().join('');
        if (!wordMap.has(sortedWord)) {
            wordMap.set(sortedWord, []);
        }
        wordMap.get(sortedWord).push(word);
    }

    const groupedAnagrams = Array.from(wordMap.values()).map(group => group.sort());

    // Sort groups by their first word alphabetically
    groupedAnagrams.sort((a, b) => a[0].localeCompare(b[0]));

    return groupedAnagrams;
}