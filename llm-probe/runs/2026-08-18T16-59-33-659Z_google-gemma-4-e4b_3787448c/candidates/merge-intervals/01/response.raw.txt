export function solve(input) {
    if (!input || !input.intervals || input.intervals.length === 0) {
        return [];
    }

    // Create a shallow copy of the intervals array to ensure immutability
    const sortedIntervals = [...input.intervals];

    // Sort intervals by start time (a[0])
    sortedIntervals.sort((a, b) => a[0] - b[0]);

    let merged = [];

    // Initialize the working interval with the first element
    let currentStart = sortedIntervals[0][0];
    let currentEnd = sortedIntervals[0][1];

    for (let i = 1; i < sortedIntervals.length; i++) {
        const [nextStart, nextEnd] = sortedIntervals[i];

        // Check for overlap or touching condition: next interval starts before or at current end
        if (nextStart <= currentEnd) {
            // Merge: update the end boundary to the maximum of the two ends
            currentEnd = Math.max(currentEnd, nextEnd);
        } else {
            // No overlap/touching: The current merged interval is complete. Save it and start a new one.
            merged.push([currentStart, currentEnd]);
            
            currentStart = nextStart;
            currentEnd = nextEnd;
        }
    }

    // Add the last accumulated interval segment
    merged.push([currentStart, currentEnd]);

    return merged;
}