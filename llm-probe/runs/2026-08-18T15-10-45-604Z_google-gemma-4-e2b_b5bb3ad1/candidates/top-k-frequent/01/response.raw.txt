export function solve(input) {
    const numbers = input.numbers;
    const k = input.k;

    if (!numbers || numbers.length === 0 || k <= 0) {
        return [];
    }

    // Step 1: Count frequencies
    const counts = {};
    for (const num of numbers) {
        counts[num] = (counts[num] || 0) + 1;
    }

    // Step 2: Get unique numbers
    const uniqueNumbers = Object.keys(counts).map(Number);

    // Step 3: Sort the unique numbers
    uniqueNumbers.sort((a, b) => {
        const freqA = counts[a];
        const freqB = counts[b];

        // Primary sort: descending frequency (freqB - freqA)
        if (freqA !== freqB) {
            return freqB - freqA;
        }
        // Secondary sort: ascending number value (a - b)
        return a - b;
    });

    // Step 4: Select the top k elements
    return uniqueNumbers.slice(0, k);
}