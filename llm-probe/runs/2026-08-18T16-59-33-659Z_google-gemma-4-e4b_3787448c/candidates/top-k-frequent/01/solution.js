export function solve(input) {
    const numbers = input.numbers;
    const k = input.k;

    // 1. Count frequencies
    const freqMap = new Map();
    for (const num of numbers) {
        freqMap.set(num, (freqMap.get(num) || 0) + 1);
    }

    // 2. Convert map entries to an array of [number, frequency] pairs
    let sortedEntries = Array.from(freqMap.entries()).map(([num, freq]) => ({ num: num, freq: freq }));

    // 3. Sort the entries
    // Sort criteria:
    // a) Descending frequency (b1 - b2 > 0 means descending) -> b2.freq - b1.freq
    // b) Tie-breaker: Ascending number value -> a1.num - a2.num
    sortedEntries.sort((a, b) => {
        // Compare frequencies (descending)
        if (b.freq !== a.freq) {
            return b.freq - a.freq;
        }
        // Frequencies are equal, compare numbers (ascending)
        return a.num - b.num;
    });

    // 4. Select the top K numbers
    const result = [];
    for (let i = 0; i < Math.min(k, sortedEntries.length); i++) {
        result.push(sortedEntries[i].num);
    }

    return result;
}