export function solve(input) {
    if (input.intervals.length === 0) return [];

    // Sort intervals by start time
    input.intervals.sort((a, b) => a[0] - b[0]);

    const mergedIntervals = [];
    let currentInterval = input.intervals[0];

    for (let i = 1; i < input.intervals.length; i++) {
        const interval = input.intervals[i];
        
        if (interval[0] <= currentInterval[1]) {
            // Overlap or touching, merge the intervals
            currentInterval[1] = Math.max(currentInterval[1], interval[1]);
        } else {
            // No overlap, add the current interval to the merged list
            mergedIntervals.push(currentInterval);
            currentInterval = interval;
        }
    }

    // Add the last interval after the loop
    mergedIntervals.push(currentInterval);

    return mergedIntervals;
}