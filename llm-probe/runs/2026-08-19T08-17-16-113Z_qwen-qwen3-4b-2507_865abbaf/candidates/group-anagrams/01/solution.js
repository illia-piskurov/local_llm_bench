export function solve(input) {
    if (!input || !Array.isArray(input.words)) {
        return [];
    }
    
    const wordMap = new Map();
    
    for (const word of input.words) {
        // Sort the letters in the word to create a key
        const sortedWord = word.split('').sort().join('');
        
        if (!wordMap.has(sortedWord)) {
            wordMap.set(sortedWord, []);
        }
        
        wordMap.get(sortedWord).push(word);
    }
    
    // Sort each group of anagrams alphabetically
    for (const group of wordMap.values()) {
        group.sort();
    }
    
    // Convert map values to array of groups and sort groups by first word
    const groups = Array.from(wordMap.values());
    groups.sort((a, b) => a[0].localeCompare(b[0]));
    
    return groups;
}