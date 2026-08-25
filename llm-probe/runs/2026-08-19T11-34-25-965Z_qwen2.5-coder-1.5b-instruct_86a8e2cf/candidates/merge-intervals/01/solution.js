export function solve(input) {
  const intervals = input.intervals.sort((a, b) => a[0] - b[0]);
  let merged = [intervals[0]];
  
  for (let i = 1; i < intervals.length; i++) {
    if (merged[merged.length - 1][1] >= intervals[i][0]) {
      merged[merged.length - 1][1] = Math.max(merged[merged.length - 1][1], intervals[i][1]);
    } else {
      merged.push(intervals[i]);
    }
  }
  
  return merged;
}