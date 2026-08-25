export function solve(input) {
    const words = input.words;
    if (!words || words.length === 0) {
        return [];
    }

    /**
     * Generates a canonical key for any word by sorting its characters.
     * @param {string} word
     * @returns {string} The sorted string representation of the characters.
     */
    const getKey = (word) => {
        return [...word].sort().join('');
    };

    // Step 1 & 2: Grouping anagrams using a Map where key is the sorted form, value is an array of words.
    const groupsMap = new Map();

    for (const word of words) {
        const key = getKey(word);
        if (!groupsMap.has(key)) {
            groupsMap.set(key, []);
        }
        // Ensure we do not mutate the input array or accidentally overwrite data structures based on keys
        groupsMap.get(key).push(word);
    }

    // Step 3: Extract values (the groups) into an array.
    let resultGroups = Array.from(groupsMap.values());

    // Step 4: Sort words inside each group alphabetically (Inner Sort).
    for (let i = 0; i < resultGroups.length; i++) {
        resultGroups[i].sort();
    }

    // Step 5: Sort the groups themselves based on their first word alphabetically (Outer Sort).
    // Since we sorted the inner arrays in Step 4, the first element (index 0) is always the lexicographically smallest word for that group.
    resultGroups.sort((groupA, groupB) => {
        const comparisonWordA = groupA[0];
        const comparisonWordB = groupB[0];
        return comparisonWordA.localeCompare(comparisonWordB);
    });

    return resultGroups;
}