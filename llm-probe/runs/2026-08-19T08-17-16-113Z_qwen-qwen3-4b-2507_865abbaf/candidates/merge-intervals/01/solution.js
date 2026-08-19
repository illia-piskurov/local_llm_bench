export function solve(input) {
    const intervals = input.intervals || [];
    
    // If no intervals, return empty array
    if (intervals.length === 0) {
        return [];
    }
    
    // Sort intervals by start time
    intervals.sort((a, b) => a[0] - b[0]);
    
    const merged = [];
    let currentStart = intervals[0][0];
    let currentEnd = intervals[0][1];
    
    for (let i = 1; i < intervals.length; i++) {
        const [start, end] = intervals[i];
        
        // If current interval overlaps or touches the previous one
        if (start <= currentEnd) {
            // Merge by extending the end if necessary
            currentEnd = Math.max(currentEnd, end);
        } else {
            // No overlap, add current merged interval and start a new one
            merged.push([currentStart, currentEnd]);
            currentStart = start;
            currentEnd = end;
        }
    }
    
    // Don't forget to add the last interval
    merged.push([currentStart, currentEnd]);
    
    return merged;
}