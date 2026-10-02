export function solve(input) {
  // Make a shallow copy of intervals to avoid mutating input
  const intervals = input.intervals.slice().map(pair => [pair[0], pair[1]]);
  // Sort by start time
  intervals.sort((a, b) => a[0] - b[0]);

  const merged = [];
  for (const [start, end] of intervals) {
    if (!merged.length || merged[merged.length - 1][1] < start) {
      // No overlap or touching
      merged.push([start, end]);
    } else {
      // Overlap or touching: merge with last interval
      merged[merged.length - 1][1] = Math.max(merged[merged.length - 1][1], end);
    }
  }

  return merged;
}