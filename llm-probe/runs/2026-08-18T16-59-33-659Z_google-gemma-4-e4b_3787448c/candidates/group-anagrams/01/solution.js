export function solve(input) {
    const words = input && input.words ? [...input.words] : [];

    if (words.length === 0) {
        return [];
    }

    // Helper function to generate the canonical key for an anagram group
    const getCanonicalKey = (word) => {
        return word.split('').sort().join('');
    };

    // Step 1: Group words by their canonical key
    /** @type {Map<string, string[]>} */
    const groupsMap = new Map();

    for (const word of words) {
        const key = getCanonicalKey(word);
        if (!groupsMap.has(key)) {
            groupsMap.set(key, []);
        }
        // We push the original word into the group array
        groupsMap.get(key).push(word);
    }

    // Step 2: Extract values and sort words within each group (internal sort)
    let groups = [];
    for (const [key, wordList] of groupsMap) {
        // Sort words alphabetically (e.g., ["tea", "eat", "ate"] -> ["ate", "eat", "tea"])
        wordList.sort();
        groups.push(wordList);
    }

    // Step 3: Sort the groups based on their first word element (group sort)
    // The comparison function compares group A's first word with group B's first word
    groups.sort((a, b) => {
        const firstWordA = a[0];
        const firstWordB = b[0];
        if (firstWordA < firstWordB) return -1;
        if (firstWordA > firstWordB) return 1;
        return 0; // Should not happen given unique input words
    });

    return groups;
}