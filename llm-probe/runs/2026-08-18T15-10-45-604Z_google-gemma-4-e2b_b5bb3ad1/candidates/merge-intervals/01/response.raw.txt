export function solve(input) {
    const intervals = input.intervals;

    if (!intervals || intervals.length === 0) {
        return [];
    }

    // Create a copy and sort by the start time
    const sortedIntervals = [...intervals].sort((a, b) => a[0] - b[0]);

    const merged = [];
    let currentStart = sortedIntervals[0][0];
    let currentEnd = sortedIntervals[0][1];

    for (let i = 1; i < sortedIntervals.length; i++) {
        const nextStart = sortedIntervals[i][0];
        const nextEnd = sortedIntervals[i][1];

        // Check for overlap or touching: if the next interval starts before or at the current merged end
        if (nextStart <= currentEnd) {
            // Merge: extend the current end time
            currentEnd = Math.max(currentEnd, nextEnd);
        } else {
            // No overlap: finalize the current merged interval and start a new one
            merged.push([currentStart, currentEnd]);
            currentStart = nextStart;
            currentEnd = nextEnd;
        }
    }

    // Add the last processed interval
    merged.push([currentStart, currentEnd]);

    return merged;
}