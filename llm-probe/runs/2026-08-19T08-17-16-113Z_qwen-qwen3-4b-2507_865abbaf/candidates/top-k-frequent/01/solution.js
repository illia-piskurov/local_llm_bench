export function solve(input) {
    const numbers = input.numbers;
    const k = input.k;
    
    // Count frequency of each number
    const frequencyMap = {};
    for (const num of numbers) {
        frequencyMap[num] = (frequencyMap[num] || 0) + 1;
    }
    
    // Create array of [number, frequency] pairs
    const pairs = Object.entries(frequencyMap).map(([num, freq]) => [parseInt(num), freq]);
    
    // Sort by descending frequency, then by ascending number value
    pairs.sort((a, b) => {
        if (a[1] !== b[1]) {
            return b[1] - a[1]; // descending frequency
        }
        return a[0] - b[0]; // ascending number value
    });
    
    // Extract the first k numbers
    const result = pairs.slice(0, k).map(pair => pair[0]);
    
    return result;
}