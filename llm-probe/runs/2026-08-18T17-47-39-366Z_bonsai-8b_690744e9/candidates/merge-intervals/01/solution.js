export function solve(input) {
  const intervals = input.intervals;
  if (intervals.length === 0) return [];
  
  // Sort the intervals based on their start values
  intervals.sort((a, b) => a[0] - b[0]);
  
  // Merge overlapping or touching intervals
  let merged = [intervals[0]];
  
  for (let i = 1; i < intervals.length; i++) {
    const prev = merged[merged.length - 1];
    const current = intervals[i];
    
    if (current[0] <= prev[1]) {
      // Overlapping or touching, merge them
      merged[merged.length - 1][1] = Math.max(prev[1], current[1]);
    } else {
      // No overlap, add as a new interval
      merged.push(current);
    }
  }
  
  return merged;
}