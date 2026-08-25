export function solve(input) {
    const words = new Set(input.words);
    const groups = {};

    for (const word of words) {
        const sortedWord = [...word].sort().join('');
        if (!groups[sortedWord]) groups[sortedWord] = [];
        groups[sortedWord].push(word);
    }

    return Object.values(groups)
        .map(group => group.sort())
        .sort((a, b) => a[0].localeCompare(b[0]));
}