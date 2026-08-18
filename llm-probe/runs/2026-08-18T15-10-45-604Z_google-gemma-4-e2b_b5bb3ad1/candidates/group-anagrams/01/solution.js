export function solve(input) {
    const words = input.words;
    if (!words || words.length === 0) {
        return [];
    }

    // Step 1: Group anagrams using a Map
    const anagramGroups = new Map();

    for (const word of words) {
        // Create the canonical key by sorting the letters
        const sortedWord = word.split('').sort().join('');
        
        if (!anagramGroups.has(sortedWord)) {
            anagramGroups.set(sortedWord, []);
        }
        anagramGroups.get(sortedWord).push(word);
    }

    let resultGroups = [];

    // Step 2: Process groups (Sort words within each group)
    for (const group of anagramGroups.values()) {
        // Sort words alphabetically within the group
        group.sort();
        resultGroups.push(group);
    }

    // Step 3: Sort groups by their first word alphabetically
    resultGroups.sort((a, b) => {
        // Compare based on the first element of each group (which is the lexicographically smallest word due to step 2 sorting)
        const firstA = a[0];
        const firstB = b[0];
        
        if (firstA < firstB) {
            return -1;
        }
        if (firstA > firstB) {
            return 1;
        }
        return 0;
    });

    return resultGroups;
}