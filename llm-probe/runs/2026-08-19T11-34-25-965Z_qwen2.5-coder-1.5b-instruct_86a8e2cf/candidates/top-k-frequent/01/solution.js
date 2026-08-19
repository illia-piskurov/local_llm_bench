export function solve(input) {
    const frequencyMap = {};
    for (const num of input.numbers) {
        if (frequencyMap[num]) {
            frequencyMap[num]++;
        } else {
            frequencyMap[num] = 1;
        }
    }

    const sortedFrequencyPairs = Object.entries(frequencyMap).sort((a, b) => b[1] - a[1]);
    return sortedFrequencyPairs.slice(0, input.k).map(pair => pair[0]);
}