export function solve(input) {
    const { numbers, k } = input;
    const frequencyMap = new Map();

    for (const num of numbers) {
        frequencyMap.set(num, (frequencyMap.get(num) || 0) + 1);
    }

    return Array.from(frequencyMap.entries())
        .sort((a, b) => b[1] - a[1] || a[0] - b[0])
        .slice(0, k)
        .map(([num]) => num);
}