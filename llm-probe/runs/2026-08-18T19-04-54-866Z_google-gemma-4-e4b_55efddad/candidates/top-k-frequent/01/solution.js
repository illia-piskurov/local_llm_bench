export function solve(input) {
    const numbers = input.numbers;
    const k = input.k;

    if (!numbers || numbers.length === 0 || k <= 0) {
        return [];
    }

    // Step 1: Count Frequencies
    const counts = new Map();
    for (const num of numbers) {
        counts.set(num, (counts.get(num) || 0) + 1);
    }

    // Step 2: Convert Map entries into an array structure for sorting
    // [{ value: number, frequency: count }, ...]
    let items = [];
    for (const [value, frequency] of counts.entries()) {
        items.push({ value: value, frequency: frequency });
    }

    // Step 3: Sort the items
    // Primary sort: Descending frequency (b.frequency - a.frequency)
    // Secondary sort (Tiebreaker): Ascending number value (a.value - b.value)
    items.sort((a, b) => {
        // Compare frequencies first (descending order)
        if (a.frequency !== b.frequency) {
            return b.frequency - a.frequency; // Higher frequency comes first
        }
        // If frequencies are equal, compare values (ascending order)
        return a.value - b.value; // Smaller value comes first
    });

    // Step 4 & 5: Select Top K and extract values
    let result = [];
    for (let i = 0; i < Math.min(k, items.length); i++) {
        result.push(items[i].value);
    }

    return result;
}